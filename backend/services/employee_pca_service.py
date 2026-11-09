"""Employee petty cash advances (PCA) for companies on the employee model -- Professional
Signs / KSA (assets/docs/PCA_Professional_Documentation.pdf, PS_EMPLOYEE_PCA_COMPARISON.md).

Each employee holds one PCA in the company, used for any of their projects: an
ErpExpensePettyCashFund row with ownerType='employee', whose openingBalance is the PCA amount.
The PCA is a limit, not cash handed over. Every bill names its project OP code (for the
project-wise report), but approved petty-cash bills come off the one PCA. Employees without a
PCA (e.g. those who pay from their own pocket) file reimbursements. Requests reuse
ErpExpenseFundTopupRequest with a `kind`:

* advance: the employee's HOD (or Admin) sets the PCA amount; it is live at once (status 'set',
  a log of the change -- no approval or payment). Rows with status submitted/approved/paid are
  from the earlier HOD-proposes -> Accounts Manager approves -> pays flow and still close
  through manager_approve / pay / reject.
* topup (PDF section 7, Process 1 and 2): the employee (or their HOD) raises it with approved
  bills (submitted) -> the HOD approves (hod_approved; skipped when the HOD raised it) -> the
  Accounts Manager verifies (verified) -> the Accounts Manager pays (paid): a cash withdrawal
  from the bank, or a direct payment. Paying replenishes those bills; the advance doesn't change.

Accounts Manager = finance_manager role; who pays = the company's payer roles
(region_policy.payer_roles; Professional Signs: the Accounts Manager). Admin may act at any step. Any open step can be rejected (with
a reason) by whoever acts at it. Every step is logged in ErpExpenseTopupHistory and
notifies the next person.
"""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session, joinedload

from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseFundTopupBill,
    ErpExpenseFundTopupRequest,
    ErpExpenseHodAssignment,
    ErpExpensePettyCashFund,
    ErpExpenseRegionConfig,
    ErpExpenseTransaction,
)
from services.currency import region_base_currency
from services.fund_service import (
    _PENDING_STATUSES,
    _SPEND_STATUSES,
    _TOPUP_LOAD,
    TOPUP_OPEN_STATUSES,
    _fund_bills,
    _load_fund,
    _notify_people,
    _people_with_role,
    _role_or_admin,
    _topup_dict,
    _topup_history,
    fund_service,
    fund_to_dict,
    project_shares,
)
from services.payment_service import PAYMENT_METHODS
from services.region_policy import PAYMENT_SOURCE_LABELS, PAYMENT_SOURCES, is_employee_model, payer_roles
from services.region_scope import covers_region, user_covers, user_region_ids

ADVANCE = "advance"
TOPUP = "topup"
# Status of an advance row logging a change to an employee's PCA amount (live at once).
SET = "set"
# Steps still in progress, per kind (anything else is paid, rejected or returned).
_OPEN_STATUSES = {ADVANCE: ("submitted", "approved"), TOPUP: TOPUP_OPEN_STATUSES}


def _role(user: ErpAuthExpenseUsers) -> str:
    return user.role.role_code if user.role else ""


def _is_admin(user: ErpAuthExpenseUsers) -> bool:
    return _role(user) == "admin"


def _region(db: Session, region_id: int) -> ErpExpenseRegionConfig:
    region = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_id == region_id).first()
    if region is None:
        raise LookupError("Company not found")
    if not is_employee_model(region):
        raise ValueError(f"{region.company_name or region.region_name} doesn't use employee petty cash advances")
    return region


def _hod_department_ids(db: Session, user: ErpAuthExpenseUsers) -> set[int]:
    return {
        row.department_id
        for row in db.query(ErpExpenseHodAssignment).filter(
            ErpExpenseHodAssignment.user_id == user.user_id, ErpExpenseHodAssignment.is_active == 1
        )
    }


def _is_hod_of(db: Session, user: ErpAuthExpenseUsers, employee: Optional[ErpAuthExpenseUsers], region_id: int) -> bool:
    """The employee's own department HOD, for a company the HOD covers."""
    if employee is None or not employee.department_id or _role(user) != "hod":
        return False
    return employee.department_id in _hod_department_ids(db, user) and user_covers(db, user.user_id, region_id)


def _employee_hods(db: Session, fund: ErpExpensePettyCashFund) -> list[ErpAuthExpenseUsers]:
    employee = fund.employee
    if employee is None or not employee.department_id:
        return []
    from services.approval_service import _hods_for_department

    return _hods_for_department(db, employee.department_id, fund.region_id)


def _payers(db: Session, region: ErpExpenseRegionConfig) -> list[ErpAuthExpenseUsers]:
    people: list[ErpAuthExpenseUsers] = []
    for role in payer_roles(region):
        people.extend(_people_with_role(db, role, region.region_id))
    return people or _people_with_role(db, "admin")


def _load_request(db: Session, request_id: int) -> ErpExpenseFundTopupRequest:
    row = (
        db.query(ErpExpenseFundTopupRequest)
        .options(*_TOPUP_LOAD)
        .filter(ErpExpenseFundTopupRequest.topup_id == request_id)
        .first()
    )
    if row is None:
        raise LookupError("Request not found")
    if row.fund is None or row.fund.owner_type != "employee" or not is_employee_model(row.fund.region):
        raise ValueError("This isn't an employee petty cash advance request")
    return row


def _employee_pot(db: Session, region: ErpExpenseRegionConfig, employee_id: int) -> ErpExpensePettyCashFund:
    """The employee's one advance in this company, created empty (limit 0) on first use. An
    empty pot takes no bills until an advance is paid into it."""
    fund = fund_service.employee_advance(db, employee_id, region.region_id)
    if fund is None:
        fund = ErpExpensePettyCashFund(
            region_id=region.region_id,
            owner_type="employee",
            employee_id=employee_id,
            currency=region_base_currency(region),
            opening_balance=0.0,
            is_active=1,
        )
        db.add(fund)
        db.flush()
    return fund


def _summary(row: ErpExpenseFundTopupRequest) -> str:
    fund = row.fund
    who = fund.employee.display_name if fund and fund.employee else "an employee"
    what = "advance" if (row.kind or TOPUP) == ADVANCE else "advance top-up"
    company = fund.region.region_code if fund and fund.region else ""
    return f"{fund.currency if fund else ''} {row.amount:,.2f} {what} for {who} ({company})"


def _notify(db: Session, row: ErpExpenseFundTopupRequest, step: str, actor_id: int, comment: Optional[str]) -> None:
    fund = row.fund
    region = fund.region
    what = _summary(row)
    note = f" Comment: {comment.strip()}" if comment and comment.strip() else ""
    employee = fund.employee
    requester = row.requester
    kind = row.kind or TOPUP
    key = f"pca_{kind}_{step}_{row.topup_id}"
    if step == "requested" and kind == TOPUP:
        people, subject, body = (
            _employee_hods(db, fund) or _people_with_role(db, "admin"),
            "Advance top-up to approve",
            f"{requester.display_name if requester else 'Someone'} asked for a {what}. Please check the bills and approve.{note}",
        )
    elif step in ("requested", "hod_approved"):
        # Advance proposed by the HOD, or a top-up the HOD approved: Accounts Manager next.
        people, subject, body = (
            _role_or_admin(db, "finance_manager", region.region_id),
            "Advance to approve" if kind == ADVANCE else "Advance top-up to verify",
            f"{what} is waiting for the Accounts Manager.{note}",
        )
    elif step in ("approved", "verified"):
        people, subject, body = (
            _payers(db, region),
            "Advance to pay" if kind == ADVANCE else "Advance top-up to pay",
            f"The {what} is approved. Please pay it (bank withdrawal or direct payment) and record the payment.{note}",
        )
    else:  # paid | rejected | returned
        people, subject, body = (
            [employee, requester, *_employee_hods(db, fund)],
            f"Petty cash advance {step}" if kind == ADVANCE else f"Advance top-up {step}",
            f"The {what} was {step}.{note}",
        )
    _notify_people(db, people, key, subject, body, skip_user_id=actor_id)


def _visible_query(db: Session, user: ErpAuthExpenseUsers):
    """Employee pots in employee-model companies this user may see: their own; an HOD also
    their staff's; Accounts / Accounts Manager the companies they cover; Admin all."""
    q = (
        db.query(ErpExpensePettyCashFund)
        .join(ErpExpenseRegionConfig, ErpExpenseRegionConfig.region_id == ErpExpensePettyCashFund.region_id)
        .filter(ErpExpensePettyCashFund.owner_type == "employee", ErpExpensePettyCashFund.is_active == 1)
    )
    role = _role(user)
    if role == "admin":
        return q
    if role == "hod":
        dept_ids = _hod_department_ids(db, user)
        staff = (
            [u for (u,) in db.query(ErpAuthExpenseUsers.user_id).filter(ErpAuthExpenseUsers.department_id.in_(dept_ids))]
            if dept_ids
            else []
        )
        q = q.filter(ErpExpensePettyCashFund.employee_id.in_({user.user_id, *staff}))
    elif role in ("accountant", "finance_manager"):
        pass
    else:
        return q.filter(ErpExpensePettyCashFund.employee_id == user.user_id)
    region_ids = user_region_ids(db, user.user_id)
    if region_ids is not None:
        q = q.filter(ErpExpensePettyCashFund.region_id.in_(region_ids or {-1}))
    return q


def _visible_people(db: Session, user: ErpAuthExpenseUsers, region_id: int) -> list[ErpAuthExpenseUsers]:
    """Active people of the company this user oversees (same scope as _visible_query): an HOD
    their departments' staff, Accounts / Accounts Manager (in a company they cover) and Admin
    everyone, anyone else only themselves."""
    q = (
        db.query(ErpAuthExpenseUsers)
        .options(joinedload(ErpAuthExpenseUsers.department))
        .filter(
            ErpAuthExpenseUsers.is_active == 1,
            ErpAuthExpenseUsers.is_deleted == 0,
            covers_region(region_id),
        )
    )
    role = _role(user)
    if role == "admin":
        return q.all()
    if role in ("hod", "accountant", "finance_manager") and not user_covers(db, user.user_id, region_id):
        return []
    if role == "hod":
        dept_ids = _hod_department_ids(db, user)
        return q.filter(ErpAuthExpenseUsers.department_id.in_(dept_ids)).all() if dept_ids else []
    if role in ("accountant", "finance_manager"):
        return q.all()
    return q.filter(ErpAuthExpenseUsers.user_id == user.user_id).all()


def _parse_date(value: Optional[str]) -> datetime:
    if not value:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(value.replace("Z", ""))
    except ValueError as exc:
        raise ValueError("Payment date must be YYYY-MM-DD") from exc


class EmployeePcaService:
    # ---- reading ---------------------------------------------------------------------

    def list_advances(self, db: Session, user: ErpAuthExpenseUsers, region_id: Optional[int] = None) -> list[dict[str, Any]]:
        """Employee advances (balances) this user may see, only for employee-model companies."""
        q = _visible_query(db, user).options(
            joinedload(ErpExpensePettyCashFund.region),
            joinedload(ErpExpensePettyCashFund.employee),
            joinedload(ErpExpensePettyCashFund.topups),
        )
        if region_id:
            q = q.filter(ErpExpensePettyCashFund.region_id == region_id)
        return [fund_to_dict(db, f) for f in q.all() if is_employee_model(f.region)]

    def list_requests(
        self, db: Session, user: ErpAuthExpenseUsers, status: Optional[str] = None, kind: Optional[str] = None
    ) -> list[dict[str, Any]]:
        fund_ids = [f.fund_id for f in _visible_query(db, user).all() if is_employee_model(f.region)]
        if not fund_ids:
            return []
        q = (
            db.query(ErpExpenseFundTopupRequest)
            .options(*_TOPUP_LOAD)
            .filter(ErpExpenseFundTopupRequest.fund_id.in_(fund_ids), ErpExpenseFundTopupRequest.is_active == 1)
        )
        if status:
            q = q.filter(ErpExpenseFundTopupRequest.status == status)
        if kind:
            q = q.filter(ErpExpenseFundTopupRequest.kind == kind)
        rows = q.order_by(ErpExpenseFundTopupRequest.created_on.desc()).all()
        return [_topup_dict(db, r, full_fund=False) for r in rows]

    def staff(self, db: Session, user: ErpAuthExpenseUsers, region_id: int) -> list[dict[str, Any]]:
        """People this user may propose an advance for in this company: an HOD's own
        department staff, or (Admin) anyone who belongs to the company."""
        region = _region(db, region_id)
        q = (
            db.query(ErpAuthExpenseUsers)
            .options(joinedload(ErpAuthExpenseUsers.department))
            .filter(
                ErpAuthExpenseUsers.is_active == 1,
                ErpAuthExpenseUsers.is_deleted == 0,
                covers_region(region.region_id),
            )
        )
        if _is_admin(user):
            pass
        elif _role(user) == "hod" and user_covers(db, user.user_id, region.region_id):
            dept_ids = _hod_department_ids(db, user)
            if not dept_ids:
                return []
            # An HOD doesn't set their own petty cash (Admin does).
            q = q.filter(
                ErpAuthExpenseUsers.department_id.in_(dept_ids), ErpAuthExpenseUsers.user_id != user.user_id
            )
        else:
            raise PermissionError("Only an HOD or Admin can set petty cash")
        people = sorted(q.all(), key=lambda u: (u.display_name or "").lower())
        limits = {
            employee_id: float(balance or 0)
            for employee_id, balance in db.query(
                ErpExpensePettyCashFund.employee_id, ErpExpensePettyCashFund.opening_balance
            )
            .filter(
                ErpExpensePettyCashFund.region_id == region.region_id,
                ErpExpensePettyCashFund.owner_type == "employee",
                ErpExpensePettyCashFund.is_active == 1,
            )
            .order_by(ErpExpensePettyCashFund.fund_id.desc())  # oldest wins, as employee_advance
        }
        return [
            {
                "id": u.user_id,
                "display_name": u.display_name,
                "department_name": u.department.department_name if u.department else None,
                "advance": round(limits.get(u.user_id, 0.0), 2),  # current petty cash, 0 = not set
            }
            for u in people
        ]

    def departments(self, db: Session, user: ErpAuthExpenseUsers, region_id: int) -> dict[str, Any]:
        """Light list for the Employees tab: each department this user oversees with how many
        employees it has, how many have petty cash, and the total limit. No bill figures (those
        cost a query per employee), so it loads fast; department_employees has the detail."""
        region = _region(db, region_id)
        people = _visible_people(db, user, region.region_id)
        limits = {
            employee_id: float(balance or 0)
            for employee_id, balance in db.query(
                ErpExpensePettyCashFund.employee_id, ErpExpensePettyCashFund.opening_balance
            )
            .filter(
                ErpExpensePettyCashFund.region_id == region.region_id,
                ErpExpensePettyCashFund.owner_type == "employee",
                ErpExpensePettyCashFund.is_active == 1,
            )
            .order_by(ErpExpensePettyCashFund.fund_id.desc())  # oldest wins, as employee_advance
        }
        groups: dict[int, dict[str, Any]] = {}
        for person in people:
            dept = person.department
            key = dept.department_id if dept else 0
            g = groups.setdefault(key, {
                "department_id": key,
                "department_name": dept.department_name if dept else "No department",
                "employee_count": 0,
                "with_petty_cash": 0,
                "total_limit": 0.0,
            })
            g["employee_count"] += 1
            limit = limits.get(person.user_id, 0.0)
            if limit > 0:
                g["with_petty_cash"] += 1
                g["total_limit"] = round(g["total_limit"] + limit, 2)
        rows = sorted(groups.values(), key=lambda g: g["department_name"].lower())
        for g in rows:
            g["not_set"] = g["employee_count"] - g["with_petty_cash"]
        return {
            "region_id": region.region_id,
            "region_code": region.region_code,
            "company_name": region.company_name or region.region_name,
            "currency": region_base_currency(region),
            "departments": rows,
        }

    def department_employees(
        self, db: Session, user: ErpAuthExpenseUsers, region_id: int, department_id: int
    ) -> dict[str, Any]:
        """One department's employees (department_id 0 = no department) with their petty cash
        figures -- loaded only when that department is opened."""
        region = _region(db, region_id)
        people = [
            p for p in _visible_people(db, user, region.region_id)
            if (p.department_id or 0) == department_id
        ]
        ids = [p.user_id for p in people]
        funds: dict[int, ErpExpensePettyCashFund] = {}
        if ids:
            for f in (
                db.query(ErpExpensePettyCashFund)
                .options(joinedload(ErpExpensePettyCashFund.topups), joinedload(ErpExpensePettyCashFund.region))
                .filter(
                    ErpExpensePettyCashFund.region_id == region.region_id,
                    ErpExpensePettyCashFund.owner_type == "employee",
                    ErpExpensePettyCashFund.is_active == 1,
                    ErpExpensePettyCashFund.employee_id.in_(ids),
                )
                .order_by(ErpExpensePettyCashFund.fund_id.desc())
            ):
                funds[f.employee_id] = f
        money = ("advance", "advance_waiting", "spent", "unreplenished_spend", "pending_bills", "pending_topup", "available")
        employees = []
        for person in people:
            fund = funds.get(person.user_id)
            row = {"fund_id": None, "employee_id": person.user_id, "employee_name": person.display_name,
                   **{k: 0.0 for k in money}}
            if fund is not None:
                figures = fund_to_dict(db, fund)
                waiting = round(sum(
                    t.amount for t in fund.topups
                    if (t.kind or TOPUP) == ADVANCE and t.status in _OPEN_STATUSES[ADVANCE] and t.is_active == 1
                ), 2)
                row.update({
                    "fund_id": fund.fund_id,
                    "advance": figures["approved_limit"],
                    "advance_waiting": waiting,
                    "spent": figures["spent"],
                    "unreplenished_spend": figures["unreplenished_spend"],
                    "pending_bills": figures["pending_bills"],
                    "pending_topup": figures["pending_topup"],
                    "available": figures["available"],
                })
            employees.append(row)
        employees.sort(key=lambda e: (e["employee_name"] or "").lower())
        dept = people[0].department if people else None
        return {
            "region_id": region.region_id,
            "currency": region_base_currency(region),
            "department_id": department_id,
            "department_name": dept.department_name if dept else "No department",
            "employees": employees,
        }

    def summary(self, db: Session, user: ErpAuthExpenseUsers, region_id: int) -> dict[str, Any]:
        """Report only (no fund of its own): one company's employees by department -- every
        employee this user oversees, with their petty cash figures (all 0 when none is set),
        and petty-cash spend by project (each
        project with the employees whose bills named it -- the advance itself covers all
        projects, so a project shows only `spent` and `pending_bills`). Same visibility as
        list_advances (an HOD sees their own staff).

        An advance counts once it is proposed: `advance_waiting` is proposed/approved but not
        yet paid; the other figures come from the paid advance (fund_to_dict)."""
        region = _region(db, region_id)
        funds = (
            _visible_query(db, user)
            .options(
                joinedload(ErpExpensePettyCashFund.region),
                joinedload(ErpExpensePettyCashFund.employee).joinedload(ErpAuthExpenseUsers.department),
                joinedload(ErpExpensePettyCashFund.topups),
            )
            .filter(ErpExpensePettyCashFund.region_id == region.region_id)
            .all()
        )
        rows = []
        project_rows: list[dict[str, Any]] = []
        for fund in funds:
            waiting = round(
                sum(
                    t.amount for t in fund.topups
                    if (t.kind or TOPUP) == ADVANCE and t.status in _OPEN_STATUSES[ADVANCE] and t.is_active == 1
                ),
                2,
            )
            if float(fund.opening_balance or 0) <= 0 and waiting <= 0:
                continue  # never paid and nothing waiting (e.g. a rejected proposal)
            figures = fund_to_dict(db, fund)
            employee = fund.employee
            dept = employee.department if employee else None
            rows.append({
                "fund_id": fund.fund_id,
                "employee_id": fund.employee_id,
                "employee_name": employee.display_name if employee else None,
                "department_id": dept.department_id if dept else None,
                "department_name": dept.department_name if dept else "No department",
                "advance": figures["approved_limit"],
                "advance_waiting": waiting,
                "spent": figures["spent"],
                "unreplenished_spend": figures["unreplenished_spend"],
                "pending_bills": figures["pending_bills"],
                "pending_topup": figures["pending_topup"],
                "available": figures["available"],
            })
            # The same employee's petty-cash bills, split by the project each line names.
            for txn, _part in _fund_bills(db, fund, _SPEND_STATUSES + _PENDING_STATUSES):
                spent = txn.status in _SPEND_STATUSES
                for op, amount in project_shares(txn, fund.currency).items():
                    project_rows.append({
                        "op_number": op,
                        "employee_id": fund.employee_id,
                        "employee_name": employee.display_name if employee else None,
                        "department_name": dept.department_name if dept else "No department",
                        "spent": amount if spent else 0.0,
                        "pending_bills": 0.0 if spent else amount,
                    })

        money = ("advance", "advance_waiting", "spent", "unreplenished_spend", "pending_bills", "pending_topup", "available")

        # Everyone else this user oversees, with no petty cash set yet (so the HOD / Accounts
        # Manager sees who still needs an amount).
        listed = {r["employee_id"] for r in rows}
        for person in _visible_people(db, user, region.region_id):
            if person.user_id in listed:
                continue
            dept = person.department
            rows.append({
                "fund_id": None,
                "employee_id": person.user_id,
                "employee_name": person.display_name,
                "department_id": dept.department_id if dept else None,
                "department_name": dept.department_name if dept else "No department",
                **{k: 0.0 for k in money},
            })

        def totals(items: list[dict[str, Any]]) -> dict[str, Any]:
            out = {k: round(sum(i.get(k, 0.0) for i in items), 2) for k in money}
            out["employee_count"] = len({i["employee_id"] for i in items})
            # Employees who have petty cash (set, or still waiting on an older proposal).
            out["advance_count"] = sum(
                1 for i in items if "fund_id" in i and (i["advance"] > 0 or i["advance_waiting"] > 0)
            )
            return out

        departments: dict[Any, list[dict[str, Any]]] = {}
        for r in rows:
            departments.setdefault(r["department_id"], []).append(r)
        by_department = sorted(
            (
                {
                    "department_id": items[0]["department_id"],
                    "department_name": items[0]["department_name"],
                    **totals(items),
                    "employees": sorted(
                        ({k: v for k, v in r.items() if k != "department_id"} for r in items),
                        key=lambda e: e["employee_name"] or "",
                    ),
                }
                for items in departments.values()
            ),
            key=lambda g: (g["department_name"] or "~").lower(),
        )

        projects: dict[Optional[str], dict[int, dict[str, Any]]] = {}
        for r in project_rows:
            people = projects.setdefault(r["op_number"], {})
            member = people.setdefault(
                r["employee_id"],
                {k: r[k] for k in ("employee_id", "employee_name", "department_name")} | {"spent": 0.0, "pending_bills": 0.0},
            )
            member["spent"] = round(member["spent"] + r["spent"], 2)
            member["pending_bills"] = round(member["pending_bills"] + r["pending_bills"], 2)
        by_project = sorted(
            (
                {
                    "op_number": op,
                    "op_name": None,
                    **totals(list(people.values())),
                    "employees": sorted(people.values(), key=lambda e: e["employee_name"] or ""),
                }
                for op, people in projects.items()
            ),
            key=lambda g: -(g["spent"] + g["pending_bills"]),
        )

        return {
            "region_id": region.region_id,
            "region_code": region.region_code,
            "company_name": region.company_name or region.region_name,
            "currency": region_base_currency(region),
            "totals": {**totals(rows), "project_count": len([op for op in projects if op])},
            "by_department": by_department,
            "by_project": by_project,
        }

    def request_to_dict(self, db: Session, request_id: int) -> dict[str, Any]:
        return _topup_dict(db, _load_request(db, request_id), full_fund=True)

    def replenishable_bills(self, db: Session, user: ErpAuthExpenseUsers, fund_id: int) -> list[dict[str, Any]]:
        fund = _load_fund(db, fund_id)
        self._require_can_raise_topup(db, user, fund)
        return fund_service.list_replenishable_bills_unchecked(db, fund)

    # ---- advance ---------------------------------------------------------------------

    def set_advance(
        self,
        db: Session,
        user: ErpAuthExpenseUsers,
        *,
        region_id: int,
        employee_id: int,
        amount: float,
        remarks: Optional[str] = None,
    ) -> dict[str, Any]:
        """The employee's HOD (or Admin) sets their PCA amount. A PCA is a limit, not cash handed
        over, so it is live at once: no Accounts Manager approval or payment. Money only moves
        when a top-up (approved bills) or a reimbursement is paid. One PCA per employee, used
        for all their projects; it can be raised or lowered, but not below the bills it already
        carries (spent and not topped up, or still in approval).

        Logged as an advance request with status 'set' and amount = the change (negative when
        lowered), so the history shows who changed it, when, from what and to what."""
        region = _region(db, region_id)
        employee = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == employee_id).first()
        if employee is None:
            raise LookupError("Employee not found")
        if not _is_admin(user) and not _is_hod_of(db, user, employee, region.region_id):
            raise PermissionError("Only the employee's HOD (or Admin) can set their petty cash amount")
        if not _is_admin(user) and employee.user_id == user.user_id:
            raise PermissionError("You can't set your own petty cash; ask Admin")
        new = round(float(amount or 0), 2)
        if new < 0:
            raise ValueError("The petty cash amount can't be negative")
        fund = _employee_pot(db, region, employee.user_id)
        old = round(float(fund.opening_balance or 0), 2)
        if new == old:
            raise ValueError(f"{employee.display_name}'s petty cash is already {fund.currency} {new:,.2f}")
        figures = fund_to_dict(db, fund)
        carried = round(float(figures["unreplenished_spend"] or 0) + float(figures["pending_bills"] or 0), 2)
        if new < carried:
            raise ValueError(
                f"{employee.display_name} has {fund.currency} {carried:,.2f} of bills not yet topped up; "
                "the amount can't be lower than that"
            )
        now = datetime.utcnow()
        row = ErpExpenseFundTopupRequest(
            fund_id=fund.fund_id,
            kind=ADVANCE,
            amount=round(new - old, 2),
            requester_id=user.user_id,
            status=SET,
            remarks=(remarks or "").strip() or None,
            decided_by=user.user_id,
            decided_on=now,
            is_active=1,
        )
        db.add(row)
        fund.opening_balance = new
        db.flush()
        note = f"Set to {fund.currency} {new:,.2f} (was {old:,.2f})"
        _topup_history(db, row, user.user_id, SET, " · ".join(p for p in [note, (remarks or "").strip()] if p))
        db.commit()
        _notify_people(
            db, [employee, *_employee_hods(db, fund)],
            f"pca_advance_set_{row.topup_id}", "Petty cash amount set",
            f"{employee.display_name}'s petty cash ({region.region_code}) is now {fund.currency} {new:,.2f}. "
            "Petty-cash bills come off it; top up with the approved bills when it runs low.",
            skip_user_id=user.user_id,
        )
        return self.request_to_dict(db, row.topup_id)

    # ---- top-up ----------------------------------------------------------------------

    def _require_can_raise_topup(self, db: Session, user: ErpAuthExpenseUsers, fund: ErpExpensePettyCashFund) -> None:
        if fund.owner_type != "employee" or not is_employee_model(fund.region):
            raise ValueError("This isn't an employee petty cash advance")
        if _is_admin(user) or fund.employee_id == user.user_id:
            return
        if _is_hod_of(db, user, fund.employee, fund.region_id):
            return
        raise PermissionError("Only the employee, their HOD or Admin can raise this top-up")

    def request_topup(
        self,
        db: Session,
        user: ErpAuthExpenseUsers,
        fund_id: int,
        transaction_ids: list[int],
        remarks: Optional[str] = None,
    ) -> dict[str, Any]:
        """Retired for Professional Signs: approved petty-cash bills now go straight to the
        Accounts Manager's Payments list, and paying them tops the PCA up (PDF section 7:
        HOD -> Accounts Manager -> withdrawal / direct payment -> Top-Up PCA, where the first
        two steps are the bill approvals). Requests raised before stay closable with
        hod_approve / manager_approve / pay / reject."""
        fund = _load_fund(db, fund_id)
        self._require_can_raise_topup(db, user, fund)
        raise ValueError(
            "No top-up request is needed: once your bills are approved, the Accounts Manager pays "
            "them from Payments and your petty cash is refilled"
        )
        ids = list(dict.fromkeys(int(i) for i in (transaction_ids or []) if i))
        if not ids:
            raise ValueError("Pick the approved bills this top-up is for")
        taken = fund_service._linked_transaction_ids(db, fund_id)
        if set(ids) & taken:
            raise ValueError("One of the bills is already on another top-up")
        parts = {tx.transaction_id: p for tx, p in _fund_bills(db, fund, _SPEND_STATUSES)}
        missing = [i for i in ids if i not in parts]
        if missing:
            raise ValueError("Only this employee's fully approved petty-cash bills can be topped up")
        amount = round(sum(parts[i] for i in ids), 2)
        by_hod = _is_hod_of(db, user, fund.employee, fund.region_id)
        row = ErpExpenseFundTopupRequest(
            fund_id=fund_id,
            kind=TOPUP,
            amount=amount,
            requester_id=user.user_id,
            status="hod_approved" if by_hod else "submitted",
            remarks=(remarks or "").strip() or None,
            is_active=1,
        )
        if by_hod:
            row.hod_approved_by = user.user_id
            row.hod_approved_on = datetime.utcnow()
        db.add(row)
        db.flush()
        for transaction_id in ids:
            db.add(ErpExpenseFundTopupBill(topup_id=row.topup_id, transaction_id=transaction_id, amount=parts[transaction_id]))
        _topup_history(db, row, user.user_id, "requested", remarks)
        if by_hod:
            _topup_history(db, row, user.user_id, "hod_approved", None)
        db.commit()
        row = _load_request(db, row.topup_id)
        _notify(db, row, "hod_approved" if by_hod else "requested", user.user_id, remarks)
        return self.request_to_dict(db, row.topup_id)

    def hod_approve(self, db: Session, user: ErpAuthExpenseUsers, request_id: int, remarks: Optional[str]) -> dict[str, Any]:
        """PDF step 1: HOD verifier approval of the top-up."""
        row = _load_request(db, request_id)
        if (row.kind or TOPUP) != TOPUP or row.status != "submitted":
            raise ValueError("Only a top-up waiting for the HOD can be approved here")
        if not _is_admin(user) and not _is_hod_of(db, user, row.fund.employee, row.fund.region_id):
            raise PermissionError("Only the employee's HOD can approve this top-up")
        row.status = "hod_approved"
        row.hod_approved_by = user.user_id
        row.hod_approved_on = datetime.utcnow()
        _topup_history(db, row, user.user_id, "hod_approved", remarks)
        db.commit()
        _notify(db, row, "hod_approved", user.user_id, remarks)
        return self.request_to_dict(db, request_id)

    # ---- Accounts Manager ------------------------------------------------------------

    def manager_approve(self, db: Session, user: ErpAuthExpenseUsers, request_id: int, remarks: Optional[str]) -> dict[str, Any]:
        """Accounts Manager: final approval of an advance (submitted -> approved), or
        verification of a top-up the HOD approved (hod_approved -> verified)."""
        row = _load_request(db, request_id)
        self._require_manager(db, user, row)
        kind = row.kind or TOPUP
        if kind == ADVANCE and row.status == "submitted":
            row.status, step = "approved", "approved"
        elif kind == TOPUP and row.status == "hod_approved":
            row.status, step = "verified", "verified"
        else:
            raise ValueError("This request isn't waiting for the Accounts Manager")
        row.verified_by = user.user_id
        row.verified_on = datetime.utcnow()
        _topup_history(db, row, user.user_id, step, remarks)
        db.commit()
        _notify(db, row, step, user.user_id, remarks)
        return self.request_to_dict(db, request_id)

    def _require_manager(self, db: Session, user: ErpAuthExpenseUsers, row: ErpExpenseFundTopupRequest) -> None:
        if _is_admin(user):
            return
        if _role(user) != "finance_manager":
            raise PermissionError("Only the Accounts Manager can approve this")
        if not user_covers(db, user.user_id, row.fund.region_id):
            raise PermissionError("This request belongs to a company you don't handle")

    # ---- Accounts Department ---------------------------------------------------------

    def pay(
        self,
        db: Session,
        user: ErpAuthExpenseUsers,
        request_id: int,
        *,
        payment_source: str,
        payment_method: str,
        payment_reference: str,
        payment_date: Optional[str] = None,
        remarks: Optional[str] = None,
    ) -> dict[str, Any]:
        """Accounts Department records the payment (PDF section 7: cash withdrawal from the bank,
        or direct payment by the Accounts Department). An advance raises the employee's
        advance by the amount; a top-up replenishes its bills."""
        row = _load_request(db, request_id)
        fund = row.fund
        region = fund.region
        if not _is_admin(user):
            if _role(user) not in payer_roles(region):
                raise PermissionError("Only the Accounts Manager can record this payment")
            if not user_covers(db, user.user_id, fund.region_id):
                raise PermissionError("This request belongs to a company you don't handle")
        kind = row.kind or TOPUP
        ready = "approved" if kind == ADVANCE else "verified"
        if row.status != ready:
            raise ValueError("The Accounts Manager must approve this before it is paid")
        source = (payment_source or "").strip().lower()
        if source not in PAYMENT_SOURCES:
            raise ValueError("Say where the money came from: the bank, or the Accounts Department's petty cash")
        method = (payment_method or "").strip().lower()
        if method not in PAYMENT_METHODS:
            raise ValueError(f"Payment method must be one of: {', '.join(PAYMENT_METHODS)}")
        reference = (payment_reference or "").strip()
        if not reference:
            raise ValueError("Enter the payment reference (transfer or withdrawal number)")
        paid_on = _parse_date(payment_date)
        if paid_on.date() > datetime.utcnow().date():
            raise ValueError("The payment date can't be in the future")
        row.status = "paid"
        row.payment_source = source
        row.payment_method = method
        row.payment_reference = reference[:128]
        row.payment_date = paid_on
        row.paid_by = user.user_id
        row.decided_by = user.user_id
        row.decided_on = datetime.utcnow()
        if kind == ADVANCE:
            fund.opening_balance = round(float(fund.opening_balance or 0) + float(row.amount), 2)
        note = f"Paid from {PAYMENT_SOURCE_LABELS[source]} ({method}, ref {reference})"
        _topup_history(db, row, user.user_id, "paid", " · ".join(p for p in [note, (remarks or "").strip()] if p))
        db.commit()
        _notify(db, row, "paid", user.user_id, remarks)
        return self.request_to_dict(db, request_id)

    # ---- ending a request ------------------------------------------------------------

    def reject(self, db: Session, user: ErpAuthExpenseUsers, request_id: int, comment: Optional[str]) -> dict[str, Any]:
        """Whoever acts at the current step may reject it, with a reason. A rejected top-up
        frees its bills for a new request."""
        if not comment or not comment.strip():
            raise ValueError("Say why it is being rejected")
        row = _load_request(db, request_id)
        kind = row.kind or TOPUP
        if row.status not in _OPEN_STATUSES[kind]:
            raise ValueError("This request is already closed")
        if _is_admin(user):
            pass
        elif kind == TOPUP and row.status == "submitted":
            if not _is_hod_of(db, user, row.fund.employee, row.fund.region_id):
                raise PermissionError("Only the employee's HOD can reject this top-up now")
        elif (kind == ADVANCE and row.status == "submitted") or (kind == TOPUP and row.status == "hod_approved"):
            self._require_manager(db, user, row)
        else:
            raise PermissionError("Only Admin can reject a request that is already approved for payment")
        row.status = "rejected"
        row.decided_by = user.user_id
        row.decided_on = datetime.utcnow()
        _topup_history(db, row, user.user_id, "rejected", comment)
        db.commit()
        _notify(db, row, "rejected", user.user_id, comment)
        return self.request_to_dict(db, request_id)


employee_pca_service = EmployeePcaService()

import json
from typing import Any, Optional

from sqlalchemy import bindparam, or_, text
from sqlalchemy.orm import Session, joinedload

from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseApproverDelegation,
    ErpExpenseCategory,
    ErpExpenseDepartment,
    ErpExpenseHodAssignment,
    ErpExpenseMultiRegionUserRegion,
    ErpExpenseRegionConfig,
    ErpMasterExpenseRole,
)
from services.currency import default_base_currency, region_base_currency
from auth.security import APPROVER_ROLES
from services.region_policy import matrix_stages, pca_model
from services.region_scope import covers_region


def department_to_dict(d: ErpExpenseDepartment) -> dict[str, Any]:
    return {"id": d.department_id, "name": d.department_name, "is_active": bool(d.is_active)}


def region_to_dict(r: ErpExpenseRegionConfig) -> dict[str, Any]:
    return {
        "id": r.region_id,
        "region_code": r.region_code,
        "region_name": r.region_name,
        "allocation_model": r.allocation_model,
        "approval_matrix": json.loads(r.approval_matrix_json) if r.approval_matrix_json else None,
        "petty_cash_hard_limit_enabled": bool(r.petty_cash_hard_limit_enabled),
        "company_name": r.company_name,
        "logo_url": r.logo_url,
        "brand_color": r.brand_color,
        "base_currency": region_base_currency(r),
        # 'employee' = per-employee, per-project advances (Professional Signs); else 'department'.
        "pca_model": pca_model(r),
        "is_active": bool(r.is_active),
    }


def _clean_currency(value: Optional[str]) -> str:
    code = (value or "").strip().upper()
    if len(code) != 3 or not code.isalpha():
        raise ValueError("Base currency must be a 3-letter code like AED")
    return code


def category_to_dict(c: ErpExpenseCategory) -> dict[str, Any]:
    return {
        "id": c.category_id,
        "name": c.category_name,
        "name_ar": c.category_name_ar,
        "owning_department_id": c.owning_department_id,
        "is_active": bool(c.is_active),
    }


def hod_assignment_to_dict(a: ErpExpenseHodAssignment) -> dict[str, Any]:
    return {
        "id": a.hod_assignment_id,
        "user_id": a.user_id,
        "department_id": a.department_id,
        "is_active": bool(a.is_active),
    }


def delegation_to_dict(d: ErpExpenseApproverDelegation) -> dict[str, Any]:
    return {
        "id": d.delegation_id,
        "approver_id": d.approver_id,
        "backup_id": d.backup_id,
        "start_date": d.start_date,
        "end_date": d.end_date,
    }


def _assigned_regions_by_user_id(db: Session, user_ids: list[int]) -> dict[int, list[str]]:
    if not user_ids:
        return {}
    rows = (
        db.query(ErpExpenseMultiRegionUserRegion.user_id, ErpExpenseRegionConfig.region_code)
        .join(
            ErpExpenseRegionConfig,
            ErpExpenseRegionConfig.region_id == ErpExpenseMultiRegionUserRegion.region_id,
        )
        .filter(
            ErpExpenseMultiRegionUserRegion.user_id.in_(user_ids),
            ErpExpenseMultiRegionUserRegion.is_active == 1,
        )
        .all()
    )
    out: dict[int, list[str]] = {}
    for uid, code in rows:
        if code:
            out.setdefault(int(uid), []).append(code)
    return out


def _assigned_user_ids_for_region(db: Session, region_code: str) -> list[int]:
    wanted = (region_code or "").strip().upper()
    region = (
        db.query(ErpExpenseRegionConfig)
        .filter(ErpExpenseRegionConfig.region_code == wanted)
        .first()
    )
    if not region:
        return []
    rows = (
        db.query(ErpExpenseMultiRegionUserRegion.user_id)
        .filter(
            ErpExpenseMultiRegionUserRegion.region_id == region.region_id,
            ErpExpenseMultiRegionUserRegion.is_active == 1,
        )
        .all()
    )
    return [int(row[0]) for row in rows if row[0] is not None]


def _user_ids_for_region(db: Session, region_code: str) -> set[int]:
    """Local expense-app users in this company. Used only when ERP directory is unreachable."""
    ids: set[int] = set(_assigned_user_ids_for_region(db, region_code))
    from auth.security import ERP_SUBSIDIARY_TO_REGION_CODE

    wanted = (region_code or "").strip().upper()
    codes = [code for code, mapped in ERP_SUBSIDIARY_TO_REGION_CODE.items() if mapped == wanted]
    if codes:
        stmt = text(
            """
            SELECT eu.userId
            FROM ErpAuthExpenseUsers eu
            JOIN ErpMasterEmployee me ON me.userId = eu.userId
            JOIN ErpMasterRegion r ON r.regionId = me.regionId
            JOIN ErpMasterSubsidiary s ON s.subsidiaryId = r.subsidiaryId
            WHERE eu.isDeleted = 0
              AND s.subsidiaryCode IN :codes
            """
        ).bindparams(bindparam("codes", expanding=True))
        try:
            rows = db.execute(stmt, {"codes": codes}).all()
            ids.update(int(row[0]) for row in rows if row[0] is not None)
        except Exception:
            db.rollback()
    return ids


def _erp_display_name(
    first: Optional[str],
    last: Optional[str],
    username: Optional[str],
    fallback_id: int,
    email: Optional[str] = None,
) -> str:
    name = " ".join(part.strip() for part in [first or "", last or ""] if part and part.strip())
    if name:
        return name
    if username and username.strip():
        return username.strip()
    if email and email.strip():
        return email.strip()
    return f"Employee {fallback_id}"


def _empty_people_page(limit: int, offset: int) -> dict[str, Any]:
    return {"items": [], "total": 0, "limit": limit, "offset": offset}


def _home_regions_by_user_id(db: Session, user_ids: list[int]) -> dict[int, str]:
    """ERP subsidiary → app company for these local user ids. Empty if ERP is unreachable."""
    if not user_ids:
        return {}
    from auth.security import ERP_SUBSIDIARY_TO_REGION_CODE

    stmt = text(
        """
        SELECT me.userId, s.subsidiaryCode
        FROM ErpMasterEmployee me
        JOIN ErpMasterRegion r ON r.regionId = me.regionId
        JOIN ErpMasterSubsidiary s ON s.subsidiaryId = r.subsidiaryId
        WHERE me.userId IN :ids
        """
    ).bindparams(bindparam("ids", expanding=True))
    try:
        rows = db.execute(stmt, {"ids": user_ids}).all()
    except Exception:
        db.rollback()
        return {}
    out: dict[int, str] = {}
    for uid, code in rows:
        mapped = ERP_SUBSIDIARY_TO_REGION_CODE.get(code)
        if mapped:
            out[int(uid)] = mapped
    return out


class ConfigService:
    # -- Departments --
    def list_departments(self, db: Session) -> list[dict[str, Any]]:
        return [department_to_dict(d) for d in db.query(ErpExpenseDepartment).all()]

    def create_department(self, db: Session, name: str) -> dict[str, Any]:
        d = ErpExpenseDepartment(department_name=name, is_active=1)
        db.add(d)
        db.commit()
        db.refresh(d)
        return department_to_dict(d)

    # -- Regions --
    def list_regions(self, db: Session) -> list[dict[str, Any]]:
        return [region_to_dict(r) for r in db.query(ErpExpenseRegionConfig).all()]

    def create_region(self, db: Session, body: dict[str, Any]) -> dict[str, Any]:
        r = ErpExpenseRegionConfig(
            region_code=body["region_code"],
            region_name=body["region_name"],
            allocation_model=body.get("allocation_model", "petty_cash"),
            approval_matrix_json=json.dumps(body["approval_matrix"]),
            petty_cash_hard_limit_enabled=int(bool(body.get("petty_cash_hard_limit_enabled", False))),
            company_name=body.get("company_name"),
            logo_url=body.get("logo_url"),
            brand_color=body.get("brand_color"),
            base_currency=(
                _clean_currency(body["base_currency"])
                if body.get("base_currency")
                else default_base_currency(body["region_code"])
            ),
            is_active=1,
        )
        db.add(r)
        db.commit()
        db.refresh(r)
        return region_to_dict(r)

    def update_region(self, db: Session, region_id: int, body: dict[str, Any]) -> dict[str, Any]:
        r = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_id == region_id).first()
        if not r:
            raise LookupError("Region not found")
        if "region_name" in body and body["region_name"] is not None:
            r.region_name = body["region_name"]
        if "allocation_model" in body and body["allocation_model"] is not None:
            r.allocation_model = body["allocation_model"]
        if "approval_matrix" in body and body["approval_matrix"] is not None:
            r.approval_matrix_json = json.dumps(body["approval_matrix"])
        if "petty_cash_hard_limit_enabled" in body and body["petty_cash_hard_limit_enabled"] is not None:
            r.petty_cash_hard_limit_enabled = int(bool(body["petty_cash_hard_limit_enabled"]))
        if "company_name" in body:
            r.company_name = body["company_name"]
        if "logo_url" in body:
            r.logo_url = body["logo_url"]
        if "brand_color" in body:
            r.brand_color = body["brand_color"]
        if body.get("base_currency"):
            r.base_currency = _clean_currency(body["base_currency"])
        db.commit()
        db.refresh(r)
        return region_to_dict(r)

    def region_approvers(self, db: Session, region_id: int) -> dict[str, Any]:
        """Per role, who handles this company's bills (home company or Admin-assigned)."""
        region = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_id == region_id).first()
        if not region:
            raise LookupError("Region not found")
        rows = (
            db.query(ErpAuthExpenseUsers)
            .join(ErpMasterExpenseRole)
            .options(joinedload(ErpAuthExpenseUsers.role), joinedload(ErpAuthExpenseUsers.department))
            .filter(
                ErpMasterExpenseRole.role_code.in_(APPROVER_ROLES),
                ErpAuthExpenseUsers.is_active == 1,
                ErpAuthExpenseUsers.is_deleted == 0,
                covers_region(region_id),
            )
            .order_by(ErpAuthExpenseUsers.display_name)
            .all()
        )
        out: dict[str, list[dict[str, Any]]] = {role: [] for role in APPROVER_ROLES}
        for u in rows:
            out[u.role.role_code].append(
                {
                    "id": u.user_id,
                    "display_name": u.display_name,
                    "department_name": u.department.department_name if u.department else None,
                    "home_region": u.home_region_id == region_id,
                }
            )
        return {
            "region_id": region.region_id,
            "region_code": region.region_code,
            "roles": out,
            "missing": [role for role in matrix_stages(region) if role in out and role != "hod" and not out[role]],
        }

    # -- Categories --
    def list_categories(self, db: Session) -> list[dict[str, Any]]:
        return [category_to_dict(c) for c in db.query(ErpExpenseCategory).all()]

    def create_category(self, db: Session, body: dict[str, Any]) -> dict[str, Any]:
        if body.get("owning_department_id") is not None:
            if not db.query(ErpExpenseDepartment).filter(
                ErpExpenseDepartment.department_id == body["owning_department_id"]
            ).first():
                raise ValueError("owning_department_id does not exist")
        c = ErpExpenseCategory(
            category_name=body["name"],
            category_name_ar=body.get("name_ar"),
            owning_department_id=body.get("owning_department_id"),
            is_active=1,
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        return category_to_dict(c)

    def update_category(self, db: Session, category_id: int, body: dict[str, Any]) -> dict[str, Any]:
        c = db.query(ErpExpenseCategory).filter(ErpExpenseCategory.category_id == category_id).first()
        if not c:
            raise LookupError("Category not found")
        if "name" in body and body["name"] is not None:
            c.category_name = body["name"]
        if "name_ar" in body:
            c.category_name_ar = body["name_ar"]
        if "owning_department_id" in body:
            c.owning_department_id = body["owning_department_id"]
        if "is_active" in body and body["is_active"] is not None:
            c.is_active = int(bool(body["is_active"]))
        db.commit()
        db.refresh(c)
        return category_to_dict(c)

    def delete_category(self, db: Session, category_id: int) -> None:
        c = db.query(ErpExpenseCategory).filter(ErpExpenseCategory.category_id == category_id).first()
        if not c:
            raise LookupError("Category not found")
        db.delete(c)
        db.commit()

    # -- HOD assignments (Phase 2) --
    def list_hod_assignments(self, db: Session) -> list[dict[str, Any]]:
        return [hod_assignment_to_dict(a) for a in db.query(ErpExpenseHodAssignment).all()]

    def create_hod_assignment(self, db: Session, user_id: int, department_id: int) -> dict[str, Any]:
        a = ErpExpenseHodAssignment(user_id=user_id, department_id=department_id, is_active=1)
        db.add(a)
        db.commit()
        db.refresh(a)
        return hod_assignment_to_dict(a)

    # -- Approver delegations (Phase 2) --
    def list_delegations(self, db: Session) -> list[dict[str, Any]]:
        return [delegation_to_dict(d) for d in db.query(ErpExpenseApproverDelegation).all()]

    def create_delegation(self, db: Session, approver_id: int, backup_id: int, start_date: str, end_date: str) -> dict[str, Any]:
        d = ErpExpenseApproverDelegation(
            approver_id=approver_id, backup_id=backup_id, start_date=start_date, end_date=end_date
        )
        db.add(d)
        db.commit()
        db.refresh(d)
        return delegation_to_dict(d)

    # -- People / ERP directory (no local copy) --
    def list_users(
        self,
        db: Session,
        *,
        region_code: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
    ) -> dict[str, Any]:
        limit = max(1, min(int(limit or 25), 100))
        offset = max(0, int(offset or 0))
        code = (region_code or "").strip()
        if code:
            erp_page = self._list_erp_employees(db, region_code=code, q=q, limit=limit, offset=offset)
            if erp_page is not None:
                return erp_page
        return self._list_local_users(db, region_code=code or None, q=q, limit=limit, offset=offset)

    def _list_erp_employees(
        self,
        db: Session,
        *,
        region_code: str,
        q: Optional[str],
        limit: int,
        offset: int,
    ) -> Optional[dict[str, Any]]:
        """Page ErpMasterEmployee for this company. Returns None if ERP tables are unreachable."""
        from auth.security import ERP_SUBSIDIARY_TO_REGION_CODE

        wanted = region_code.strip().upper()
        codes = [c for c, mapped in ERP_SUBSIDIARY_TO_REGION_CODE.items() if mapped == wanted]
        assigned = _assigned_user_ids_for_region(db, wanted)
        if not codes and not assigned:
            return _empty_people_page(limit, offset)

        where = ["me.isDeleted = 0", "(me.isActive = 1 OR me.isActive IS NULL)"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        binds: list[Any] = []
        company_clause: list[str] = []
        if codes:
            company_clause.append("s.subsidiaryCode IN :codes")
            params["codes"] = codes
            binds.append(bindparam("codes", expanding=True))
        if assigned:
            company_clause.append("me.userId IN :assigned")
            params["assigned"] = assigned
            binds.append(bindparam("assigned", expanding=True))
        where.append("(" + " OR ".join(company_clause) + ")")
        needle = (q or "").strip()
        if needle:
            where.append(
                "("
                "me.firstName LIKE :like OR me.lastName LIKE :like "
                "OR CONCAT(ISNULL(me.firstName, ''), ' ', ISNULL(me.lastName, '')) LIKE :like "
                "OR me.emailId LIKE :like OR d.departmentName LIKE :like OR au.userName LIKE :like"
                ")"
            )
            params["like"] = f"%{needle}%"
        where_sql = " AND ".join(where)
        count_from = f"""
            FROM ErpMasterEmployee me
            LEFT JOIN ErpMasterRegion r ON r.regionId = me.regionId
            LEFT JOIN ErpMasterSubsidiary s ON s.subsidiaryId = r.subsidiaryId
            {"" if not needle else "LEFT JOIN ErpMasterDepartment d ON d.departmentId = me.departmentId LEFT JOIN ErpAuthUsers au ON au.userId = me.userId AND au.isDeleted = 0"}
            WHERE {where_sql}
        """
        page_from = f"""
            FROM ErpMasterEmployee me
            LEFT JOIN ErpMasterRegion r ON r.regionId = me.regionId
            LEFT JOIN ErpMasterSubsidiary s ON s.subsidiaryId = r.subsidiaryId
            LEFT JOIN ErpMasterDepartment d ON d.departmentId = me.departmentId
            LEFT JOIN ErpAuthUsers au ON au.userId = me.userId AND au.isDeleted = 0
            OUTER APPLY (
              SELECT TOP 1 mr.roleName, mr.roleId
              FROM ErpAuthUserRoleMap map
              JOIN ErpMasterRole mr ON mr.roleId = map.roleId AND mr.isActive = 1 AND mr.isDeleted = 0
              WHERE map.userId = me.userId AND map.isActive = 1
              ORDER BY map.mapId DESC
            ) erpRole
            WHERE {where_sql}
        """
        count_stmt = text("SELECT COUNT(*) " + count_from)
        page_stmt = text(
            """
            SELECT me.userId, me.employeeId, me.firstName, me.lastName, me.emailId,
                   d.departmentName, au.userName, s.subsidiaryCode,
                   erpRole.roleName, erpRole.roleId
            """
            + page_from
            + """
            ORDER BY CASE WHEN NULLIF(LTRIM(ISNULL(me.firstName, '') + ISNULL(me.lastName, '')), '') IS NULL THEN 1 ELSE 0 END,
                     me.firstName, me.lastName, me.employeeId
            OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """
        )
        for item in binds:
            count_stmt = count_stmt.bindparams(item)
            page_stmt = page_stmt.bindparams(item)
        try:
            total = int(db.execute(count_stmt, params).scalar() or 0)
            rows = db.execute(page_stmt, params).all()
        except Exception:
            db.rollback()
            return None
        user_ids = [
            int(row.userId) if row.userId is not None else int(row.employeeId)
            for row in rows
            if row.userId is not None or row.employeeId is not None
        ]
        local_by_id = self._local_users_by_id(db, user_ids)
        assigned = _assigned_regions_by_user_id(db, user_ids)
        return {
            "items": [
                self._erp_employee_to_dict(
                    db,
                    row,
                    home_region_code=wanted,
                    local=local_by_id.get(int(row.userId) if row.userId is not None else int(row.employeeId)),
                    region_codes=assigned.get(
                        int(row.userId) if row.userId is not None else int(row.employeeId),
                        [],
                    ),
                )
                for row in rows
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def _list_local_users(
        self,
        db: Session,
        *,
        region_code: Optional[str],
        q: Optional[str],
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        query = (
            db.query(ErpAuthExpenseUsers)
            .join(ErpMasterExpenseRole)
            .outerjoin(ErpExpenseDepartment)
            .options(
                joinedload(ErpAuthExpenseUsers.role),
                joinedload(ErpAuthExpenseUsers.department),
            )
            .filter(ErpAuthExpenseUsers.is_deleted == 0, ErpAuthExpenseUsers.is_active == 1)
        )
        if region_code:
            ids = _user_ids_for_region(db, region_code)
            if not ids:
                return _empty_people_page(limit, offset)
            query = query.filter(ErpAuthExpenseUsers.user_id.in_(ids))
        needle = (q or "").strip()
        if needle:
            like = f"%{needle}%"
            query = query.filter(
                or_(
                    ErpAuthExpenseUsers.display_name.like(like),
                    ErpAuthExpenseUsers.user_name.like(like),
                    ErpMasterExpenseRole.role_code.like(like),
                    ErpExpenseDepartment.department_name.like(like),
                )
            )
        total = query.order_by(None).count()
        rows = query.order_by(ErpAuthExpenseUsers.display_name).offset(offset).limit(limit).all()
        user_ids = [u.user_id for u in rows]
        homes = _home_regions_by_user_id(db, user_ids)
        assigned = _assigned_regions_by_user_id(db, user_ids)
        return {
            "items": [
                self.user_to_dict(
                    db,
                    u,
                    home_region_code=homes.get(u.user_id),
                    region_codes=assigned.get(u.user_id, []),
                )
                for u in rows
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def _local_users_by_id(self, db: Session, user_ids: list[int]) -> dict[int, ErpAuthExpenseUsers]:
        if not user_ids:
            return {}
        rows = (
            db.query(ErpAuthExpenseUsers)
            .options(joinedload(ErpAuthExpenseUsers.role), joinedload(ErpAuthExpenseUsers.department))
            .filter(ErpAuthExpenseUsers.user_id.in_(user_ids), ErpAuthExpenseUsers.is_deleted == 0)
            .all()
        )
        return {u.user_id: u for u in rows}

    def _erp_employee_to_dict(
        self,
        db: Session,
        row: Any,
        *,
        home_region_code: Optional[str] = None,
        local: Optional[ErpAuthExpenseUsers] = None,
        region_codes: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        from auth.security import ERP_SUBSIDIARY_TO_REGION_CODE

        user_id = int(row.userId) if row.userId is not None else int(row.employeeId)
        mapped_home = ERP_SUBSIDIARY_TO_REGION_CODE.get(row.subsidiaryCode) if row.subsidiaryCode else None
        if local is None:
            local = self._local_users_by_id(db, [user_id]).get(user_id)
        assigned = region_codes if region_codes is not None else _assigned_regions_by_user_id(db, [user_id]).get(user_id, [])
        erp_role = getattr(row, "roleName", None)
        erp_role_id = getattr(row, "roleId", None)
        from auth.security import mapped_app_role

        role = local.role.role_code if local and local.role else mapped_app_role(erp_role_id, erp_role)
        return {
            "id": user_id,
            "employee_id": int(row.employeeId) if row.employeeId is not None else None,
            "username": row.userName or (local.user_name if local else None),
            "display_name": _erp_display_name(row.firstName, row.lastName, row.userName, user_id, row.emailId),
            "role": role,
            "erp_role": erp_role,
            "department_id": local.department_id if local else None,
            "department_name": row.departmentName or (local.department.department_name if local and local.department else None),
            "email": row.emailId or (local.email if local else None),
            "home_region_code": mapped_home or home_region_code,
            "region_codes": assigned,
            "has_app_login": local is not None,
        }

    def get_user(self, db: Session, user_id: int) -> dict[str, Any]:
        erp = self._get_erp_employee(db, user_id)
        if erp is not None:
            return erp
        user = (
            db.query(ErpAuthExpenseUsers)
            .options(
                joinedload(ErpAuthExpenseUsers.role),
                joinedload(ErpAuthExpenseUsers.department),
            )
            .filter(
                ErpAuthExpenseUsers.user_id == user_id,
                ErpAuthExpenseUsers.is_deleted == 0,
            )
            .first()
        )
        if not user:
            raise LookupError("User not found")
        return self.user_to_dict(db, user)

    def _get_erp_employee(self, db: Session, user_id: int) -> Optional[dict[str, Any]]:
        stmt = text(
            """
            SELECT TOP 1 me.userId, me.employeeId, me.firstName, me.lastName, me.emailId,
                   d.departmentName, au.userName, s.subsidiaryCode,
                   erpRole.roleName, erpRole.roleId
            FROM ErpMasterEmployee me
            LEFT JOIN ErpMasterRegion r ON r.regionId = me.regionId
            LEFT JOIN ErpMasterSubsidiary s ON s.subsidiaryId = r.subsidiaryId
            LEFT JOIN ErpMasterDepartment d ON d.departmentId = me.departmentId
            LEFT JOIN ErpAuthUsers au ON au.userId = me.userId AND au.isDeleted = 0
            OUTER APPLY (
              SELECT TOP 1 mr.roleName, mr.roleId
              FROM ErpAuthUserRoleMap map
              JOIN ErpMasterRole mr ON mr.roleId = map.roleId AND mr.isActive = 1 AND mr.isDeleted = 0
              WHERE map.userId = me.userId AND map.isActive = 1
              ORDER BY map.mapId DESC
            ) erpRole
            WHERE me.isDeleted = 0 AND (me.userId = :uid OR me.employeeId = :uid)
            ORDER BY CASE WHEN me.userId = :uid THEN 0 ELSE 1 END
            """
        )
        try:
            row = db.execute(stmt, {"uid": user_id}).first()
        except Exception:
            db.rollback()
            return None
        if not row:
            return None
        return self._erp_employee_to_dict(db, row)

    def user_to_dict(
        self,
        db: Session,
        user: ErpAuthExpenseUsers,
        home_region_code: Optional[str] = None,
        region_codes: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        from auth.security import allowed_regions_for, resolve_default_region_code

        assigned = region_codes if region_codes is not None else allowed_regions_for(db, user)
        if home_region_code is None:
            try:
                home_region_code = resolve_default_region_code(db, user.user_id)
            except Exception:
                home_region_code = None
        return {
            "id": user.user_id,
            "username": user.user_name,
            "display_name": user.display_name,
            "role": user.role.role_code if user.role else None,
            "department_id": user.department_id,
            "department_name": user.department.department_name if user.department else None,
            "email": user.email,
            "home_region_code": home_region_code,
            "region_codes": assigned,
            "erp_role": None,
            "has_app_login": True,
        }

    # Roles Admin can give in People. Admin itself comes from ERP (Admin / Sub Admin).
    ASSIGNABLE_ROLES = ("employee", "hod", "accountant", "head_accountant", "finance_manager")

    def set_user_role(self, db: Session, user_id: int, role_code: str, set_by: int) -> dict[str, Any]:
        """Admin sets a person's app role (e.g. Head of Accountant, Finance Manager, which ERP
        has no role for). Login never overwrites a local role, so it sticks."""
        code = (role_code or "").strip().lower()
        if code not in self.ASSIGNABLE_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(self.ASSIGNABLE_ROLES)}")
        if user_id == set_by:
            raise ValueError("You can't change your own role")
        user = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == user_id).first()
        if not user:
            raise ValueError(
                "This person has not signed into the expense app yet. Their role can be set after first login."
            )
        role = db.query(ErpMasterExpenseRole).filter(ErpMasterExpenseRole.role_code == code).first()
        if role is None:
            raise ValueError(f"Role {code} isn't set up yet. Restart the backend to create it.")
        user.role_id = role.role_id
        db.commit()
        db.refresh(user)
        user.department  # load
        user.role
        return self.user_to_dict(db, user)

    def set_user_regions(self, db: Session, user_id: int, region_codes: list[str], assigned_by: int) -> dict[str, Any]:
        user = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == user_id).first()
        if not user:
            raise ValueError(
                "This person has not signed into the expense app yet. Extra companies can be set after first login."
            )
        wanted = {c.strip().upper() for c in region_codes if c and c.strip()}
        regions = {
            r.region_code: r
            for r in db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_code.in_(wanted)).all()
        } if wanted else {}
        missing = wanted - set(regions)
        if missing:
            raise ValueError(f"Unknown region_code: {sorted(missing)[0]}")
        existing = (
            db.query(ErpExpenseMultiRegionUserRegion)
            .filter(ErpExpenseMultiRegionUserRegion.user_id == user_id)
            .all()
        )
        by_region = {row.region_id: row for row in existing}
        keep_ids = {r.region_id for r in regions.values()}
        for row in existing:
            if row.region_id not in keep_ids:
                row.is_active = 0
        for region in regions.values():
            row = by_region.get(region.region_id)
            if row:
                row.is_active = 1
                row.assigned_by = assigned_by
            else:
                db.add(
                    ErpExpenseMultiRegionUserRegion(
                        user_id=user_id,
                        region_id=region.region_id,
                        assigned_by=assigned_by,
                        is_active=1,
                    )
                )
        db.commit()
        db.refresh(user)
        user.department  # load
        user.role
        return self.user_to_dict(db, user)

    def set_region_logo_key(self, db: Session, region_id: int, logo_key: str) -> dict[str, Any]:
        return self.update_region(db, region_id, {"logo_url": logo_key})


config_service = ConfigService()

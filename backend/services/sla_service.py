"""Approval SLA: warns the approver when a bill passes its step's time limit, and escalates to
the next step's approvers + Admin when it is still waiting one more full time limit later.

`run_sla_check` is run every few minutes by the background loop in main.py (see
`start_sla_loop`). Each bill moves 0 (on time) -> 1 (approver warned) -> 2 (escalated) per
step visit; the clock restarts whenever the bill reaches a new step or is resubmitted after a
dispute (approval_service._enter_stage)."""
import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session, joinedload

from database.models import ErpAuthExpenseUsers, ErpExpenseTransaction

logger = logging.getLogger(__name__)

SLA_ON_TIME = 0
SLA_WARNED = 1
SLA_ESCALATED = 2

# Notification type prefixes (type is String(32): prefix + base stage + epoch fits).
WARN_PREFIX = "slaw"
ESCALATE_PREFIX = "slae"


def format_duration(delta: timedelta) -> str:
    """'51 hrs', '5 hrs 20 min', '1 hr', '14 min' -- always hours, never days."""
    minutes = max(0, int(delta.total_seconds() // 60))
    hours, mins = divmod(minutes, 60)
    if hours:
        return f"{hours} hr{'s' if hours != 1 else ''}" + (f" {mins} min" if mins else "")
    return f"{mins} min"


def _type_key(prefix: str, txn: ErpExpenseTransaction) -> str:
    """Unique per bill visit to a step, so the notification dedup never swallows a later breach
    of the same step (e.g. after a dispute and resubmit)."""
    from services.department_split import stage_base

    entered = txn.stage_entered_at or txn.stage_due_at or datetime.utcnow()
    return f"{prefix}_{stage_base(txn.current_stage)}_{int(entered.timestamp())}"[:32]


def _dedupe(people: list[Optional[ErpAuthExpenseUsers]]) -> list[ErpAuthExpenseUsers]:
    seen: set[int] = set()
    out: list[ErpAuthExpenseUsers] = []
    for p in people:
        if p is not None and p.user_id not in seen:
            seen.add(p.user_id)
            out.append(p)
    return out


def escalation_recipients(db: Session, txn: ErpExpenseTransaction) -> list[ErpAuthExpenseUsers]:
    """The next step's approvers (none after the last step) plus every active Admin."""
    from services.approval_service import _active_with_role, resolve_stage_approvers, resolve_stage_sequence

    seq = resolve_stage_sequence(db, txn)
    people: list[Optional[ErpAuthExpenseUsers]] = []
    if txn.current_stage in seq:
        idx = seq.index(txn.current_stage)
        if idx + 1 < len(seq):
            people += resolve_stage_approvers(db, txn, seq[idx + 1])
    people += _active_with_role(db, "admin")
    return _dedupe(people)


def _notify(
    db: Session,
    txn: ErpExpenseTransaction,
    recipients: list[ErpAuthExpenseUsers],
    *,
    escalate: bool,
    approver_names: str,
    now: datetime,
) -> None:
    from services import email_templates, notification_service
    from services.approval_service import resolve_stage_labels
    from services.currency import bill_and_base_text
    from services.transaction_service import vendor_display_name

    label = resolve_stage_labels(txn).get(txn.current_stage, txn.current_stage)
    waiting = format_duration(now - (txn.stage_entered_at or now))
    due = txn.stage_due_at.strftime("%d %b %Y, %H:%M UTC") if txn.stage_due_at else "-"
    vendor = vendor_display_name(txn, "unknown vendor")
    ctx = email_templates.build_context(txn)
    if escalate:
        content = email_templates.sla_escalation_email(ctx, approver_names=approver_names, waiting=waiting, due=due)
        type_ = _type_key(ESCALATE_PREFIX, txn)
        subject_en = f"Escalated: approval overdue ({vendor})"
        subject_ar = f"تصعيد: تأخر الموافقة ({vendor})"
        body_en = (
            f"Claim {txn.transaction_id} for {bill_and_base_text(txn)} has been waiting {waiting} "
            f"at {label} ({approver_names or '-'}). It was due {due}. Please follow up."
        )
        body_ar = (
            f"المطالبة رقم {txn.transaction_id} بمبلغ {bill_and_base_text(txn)} في انتظار {label} "
            f"({approver_names or '-'}) منذ {waiting}. كان الموعد {due}. يرجى المتابعة."
        )
    else:
        content = email_templates.sla_warning_email(ctx, approver_names=approver_names, waiting=waiting, due=due)
        type_ = _type_key(WARN_PREFIX, txn)
        subject_en = f"Overdue: claim awaiting your approval ({vendor})"
        subject_ar = f"متأخرة: مطالبة في انتظار موافقتك ({vendor})"
        body_en = (
            f"Claim {txn.transaction_id} for {bill_and_base_text(txn)} has been waiting {waiting} "
            f"for your approval ({label}). It was due {due}."
        )
        body_ar = (
            f"المطالبة رقم {txn.transaction_id} بمبلغ {bill_and_base_text(txn)} في انتظار موافقتك "
            f"({label}) منذ {waiting}. كان الموعد {due}."
        )
    for person in recipients:
        notification_service.send(
            db, person, type_, txn.transaction_id, subject_en, subject_ar, body_en, body_ar,
            html_body_en=content.html,
        )


def run_sla_check(db: Session, now: Optional[datetime] = None) -> dict[str, int]:
    """Warns / escalates every bill past its time limit. Safe to run as often as you like:
    each bill is warned once and escalated once per step visit."""
    from services.approval_service import ACTIONABLE_STATUSES, resolve_stage_approvers, stage_sla

    now = now or datetime.utcnow()
    rows = (
        db.query(ErpExpenseTransaction)
        .options(joinedload(ErpExpenseTransaction.region), joinedload(ErpExpenseTransaction.employee))
        .filter(
            ErpExpenseTransaction.status.in_(ACTIONABLE_STATUSES),
            ErpExpenseTransaction.current_stage.isnot(None),
            ErpExpenseTransaction.stage_due_at.isnot(None),
            ErpExpenseTransaction.stage_due_at <= now,
            # NULL for bills submitted before the column existed: treat as on time.
            (ErpExpenseTransaction.sla_state.is_(None)) | (ErpExpenseTransaction.sla_state < SLA_ESCALATED),
        )
        .all()
    )
    warned = escalated = 0
    for txn in rows:
        try:
            approvers = resolve_stage_approvers(db, txn, txn.current_stage)
            names = ", ".join(a.display_name for a in approvers if a.display_name)
            state = txn.sla_state or SLA_ON_TIME
            if state < SLA_WARNED:
                _notify(db, txn, approvers, escalate=False, approver_names=names, now=now)
                state = SLA_WARNED
                warned += 1
            if state < SLA_ESCALATED and now >= txn.stage_due_at + stage_sla(db, txn):
                _notify(db, txn, escalation_recipients(db, txn), escalate=True, approver_names=names, now=now)
                state = SLA_ESCALATED
                escalated += 1
            if state != (txn.sla_state or SLA_ON_TIME):
                txn.sla_state = state
                db.commit()
        except Exception:
            db.rollback()
            logger.exception("SLA check failed for claim %s", txn.transaction_id)
    if warned or escalated:
        logger.info("SLA check: %s warned, %s escalated", warned, escalated)
    return {"checked": len(rows), "warned": warned, "escalated": escalated}


def recalculate_due_times(db: Session, region_id: int) -> int:
    """After Admin changes a company's time limits: open bills keep the time they reached their
    step, and get a due time (and alert state) under the new limit. Returns how many changed."""
    from services.approval_service import ACTIONABLE_STATUSES, stage_sla

    now = datetime.utcnow()
    changed = 0
    rows = (
        db.query(ErpExpenseTransaction)
        .filter(
            ErpExpenseTransaction.region_id == region_id,
            ErpExpenseTransaction.status.in_(ACTIONABLE_STATUSES),
            ErpExpenseTransaction.current_stage.isnot(None),
        )
        .all()
    )
    for txn in rows:
        sla = stage_sla(db, txn)
        if txn.stage_entered_at is None:
            # Older bill: best guess at when it reached this step.
            txn.stage_entered_at = (txn.stage_due_at - sla) if txn.stage_due_at else (txn.submitted_on or now)
        due = txn.stage_entered_at + sla
        if due != txn.stage_due_at:
            txn.stage_due_at = due
            # A longer limit can put the bill back on time: allow fresh alerts.
            state = txn.sla_state or SLA_ON_TIME
            if now < due:
                state = SLA_ON_TIME
            elif now < due + sla:
                state = min(state, SLA_WARNED)
            txn.sla_state = state
            changed += 1
    db.commit()
    return changed


AGE_BUCKETS = (
    ("under_1_day", "Under 24 hrs", timedelta(days=1)),
    ("1_3_days", "24–72 hrs", timedelta(days=3)),
    ("3_7_days", "72–168 hrs", timedelta(days=7)),
    ("over_7_days", "Over 168 hrs", None),
)


def _age_bucket(waiting: timedelta) -> str:
    for key, _label, limit in AGE_BUCKETS:
        if limit is None or waiting < limit:
            return key
    return AGE_BUCKETS[-1][0]


def aging_report(db: Session, region_id: Optional[int] = None) -> dict[str, Any]:
    """Every bill waiting on an approver, most overdue first, with its SLA status and age bucket."""
    from services.approval_service import (
        ACTIONABLE_STATUSES,
        approver_lookup_cache,
        resolve_stage_approvers,
        resolve_stage_labels,
        stage_sla,
    )
    from services.region_policy import company_label

    now = datetime.utcnow()
    q = (
        db.query(ErpExpenseTransaction)
        .options(
            joinedload(ErpExpenseTransaction.region),
            joinedload(ErpExpenseTransaction.employee),
            joinedload(ErpExpenseTransaction.category),
        )
        .filter(
            ErpExpenseTransaction.status.in_(ACTIONABLE_STATUSES),
            ErpExpenseTransaction.current_stage.isnot(None),
        )
    )
    if region_id is not None:
        q = q.filter(ErpExpenseTransaction.region_id == region_id)
    items: list[dict[str, Any]] = []
    with approver_lookup_cache(db):
        for txn in q.all():
            sla = stage_sla(db, txn)
            entered = txn.stage_entered_at or (txn.stage_due_at - sla if txn.stage_due_at else txn.submitted_on) or now
            due = txn.stage_due_at or entered + sla
            waiting = now - entered
            overdue = now - due
            if overdue.total_seconds() <= 0:
                status = "on_time"
            elif (txn.sla_state or 0) >= SLA_ESCALATED or now >= due + sla:
                status = "escalated"
            else:
                status = "breached"
            approvers = resolve_stage_approvers(db, txn, txn.current_stage)
            items.append(
                {
                    "transaction_id": txn.transaction_id,
                    "employee_name": txn.employee.display_name if txn.employee else None,
                    "region_id": txn.region_id,
                    "company": company_label(txn.region) if txn.region else None,
                    "vendor": txn.vendor_raw_text,
                    "total_amount": txn.total_amount,
                    "currency": txn.currency,
                    "type": txn.type,
                    "stage": txn.current_stage,
                    "stage_label": resolve_stage_labels(txn).get(txn.current_stage, txn.current_stage),
                    "approvers": [a.display_name for a in approvers],
                    "submitted_at": txn.submitted_on.isoformat() if txn.submitted_on else None,
                    "stage_entered_at": entered.isoformat(),
                    "stage_due_at": due.isoformat(),
                    "sla_hours": round(sla.total_seconds() / 3600, 2),
                    "waiting_minutes": int(waiting.total_seconds() // 60),
                    "overdue_minutes": max(0, int(overdue.total_seconds() // 60)),
                    "waiting_text": format_duration(waiting),
                    "overdue_text": format_duration(overdue) if overdue.total_seconds() > 0 else None,
                    "sla_status": status,
                    "age_bucket": _age_bucket(waiting),
                }
            )
    items.sort(key=lambda i: (-i["overdue_minutes"], -i["waiting_minutes"]))
    summary = {
        "pending": len(items),
        "on_time": sum(1 for i in items if i["sla_status"] == "on_time"),
        "breached": sum(1 for i in items if i["sla_status"] == "breached"),
        "escalated": sum(1 for i in items if i["sla_status"] == "escalated"),
        "buckets": {key: sum(1 for i in items if i["age_bucket"] == key) for key, _, _ in AGE_BUCKETS},
    }
    return {
        "generated_at": now.isoformat(),
        "summary": summary,
        "bucket_labels": {key: label for key, label, _ in AGE_BUCKETS},
        "items": items,
    }


# --- background loop --------------------------------------------------------------------

def _run_once() -> None:
    from database.models import SessionLocal

    db = SessionLocal()
    try:
        run_sla_check(db)
    except Exception:
        logger.exception("SLA check run failed")
    finally:
        db.close()


async def _loop(interval: float) -> None:
    while True:
        await asyncio.sleep(interval)
        try:
            await asyncio.to_thread(_run_once)
        except Exception:  # never let the loop die
            logger.exception("SLA loop iteration failed")


def start_sla_loop() -> Optional[asyncio.Task]:
    """Started from main.py at app startup. SLA_JOB_ENABLED=false turns it off;
    SLA_CHECK_INTERVAL_SECONDS sets how often it runs (default 5 minutes)."""
    if os.getenv("SLA_JOB_ENABLED", "true").strip().lower() in ("0", "false", "no", "off"):
        logger.info("SLA job disabled (SLA_JOB_ENABLED)")
        return None
    try:
        interval = max(30.0, float(os.getenv("SLA_CHECK_INTERVAL_SECONDS", "300")))
    except ValueError:
        interval = 300.0
    logger.info("SLA job running every %ss", int(interval))
    return asyncio.create_task(_loop(interval))  # called from an async startup hook

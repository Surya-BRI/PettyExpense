import html as html_lib
from dataclasses import dataclass
from typing import Optional

from config import get_settings

DEFAULT_BRAND_COLOR = "#32568E"
# Must match services/email_service.py's LOGO_CONTENT_ID -- the cid: the inline attachment is sent under.
LOGO_CONTENT_ID = "bri-logo"

STAGE_LABELS = {
    "hod": "Head of Department",
    "department_hod": "Department HOD",
    "accountant": "Accountant",
    "finance_manager": "Finance Manager",
}


@dataclass
class ClaimEmailContext:
    transaction_id: int
    employee_name: str
    vendor_name: str
    amount: float
    vat_amount: float
    total_amount: float
    currency: str
    bill_date: Optional[str]
    category_name: Optional[str]
    stage: Optional[str]
    employee_department: Optional[str] = None
    submitted_on: Optional[str] = None
    approver_name: Optional[str] = None
    logo_url: Optional[str] = None
    brand_color: Optional[str] = None
    comment: Optional[str] = None


@dataclass
class EmailContent:
    subject: str
    html: str
    text: str


def build_context(txn, comment: Optional[str] = None, approver=None) -> ClaimEmailContext:
    region = txn.region
    employee = txn.employee
    return ClaimEmailContext(
        transaction_id=txn.transaction_id,
        employee_name=employee.display_name if employee else "-",
        employee_department=employee.department.department_name if employee and employee.department else None,
        vendor_name=txn.vendor.vendor_name if txn.vendor else (txn.vendor_raw_text or "Unknown vendor"),
        amount=txn.amount,
        vat_amount=txn.vat_amount,
        total_amount=txn.total_amount,
        currency=txn.currency,
        bill_date=txn.bill_date,
        category_name=txn.category.category_name if txn.category else None,
        stage=txn.current_stage,
        submitted_on=txn.submitted_on.strftime("%d %b %Y, %H:%M") if txn.submitted_on else None,
        approver_name=approver.display_name if approver else None,
        logo_url=region.logo_url if region else None,
        brand_color=region.brand_color if region else None,
        comment=comment,
    )


def _money(amount: float, currency: str) -> str:
    return f"{currency} {amount:,.2f}"


def _truncate(value: str, limit: int = 70) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _stage_label(stage: Optional[str]) -> Optional[str]:
    if not stage:
        return None
    return STAGE_LABELS.get(stage, stage)


def _claim_url(transaction_id: int) -> str:
    base = get_settings().public_base_url.rstrip("/")
    return f"{base}/claims/{transaction_id}"


def _common_rows(ctx: ClaimEmailContext) -> list[tuple[str, Optional[str]]]:
    rows: list[tuple[str, Optional[str]]] = [
        ("Claim reference", f"#{ctx.transaction_id}"),
        ("Submitted by", ctx.employee_name or "-"),
        ("Department", ctx.employee_department),
        ("Submitted on", ctx.submitted_on),
        ("Vendor", _truncate(ctx.vendor_name or "-")),
        ("Amount (excl. VAT)", _money(ctx.amount, ctx.currency)),
        ("VAT amount", _money(ctx.vat_amount, ctx.currency)),
        ("Total amount", _money(ctx.total_amount, ctx.currency)),
        ("Bill date", ctx.bill_date or "-"),
        ("Category", ctx.category_name or "-"),
        ("Current stage", _stage_label(ctx.stage)),
    ]
    if ctx.approver_name:
        stage_label = _stage_label(ctx.stage)
        awaiting = f"{ctx.approver_name} ({stage_label})" if stage_label else ctx.approver_name
        rows.append(("Awaiting approval from", awaiting))
    return rows


def _row(label: str, value: Optional[str]) -> str:
    return f"""<tr>
<td style="padding:10px 14px;border-bottom:1px solid #eef0f3;font-size:13px;color:#6b7280;width:40%;font-family:Arial,Helvetica,sans-serif;">{html_lib.escape(label)}</td>
<td style="padding:10px 14px;border-bottom:1px solid #eef0f3;font-size:13px;color:#1a1a1a;font-weight:600;font-family:Arial,Helvetica,sans-serif;">{html_lib.escape(str(value))}</td>
</tr>"""


def _shell(heading: str, intro: str, rows: list[tuple[str, Optional[str]]], ctx: ClaimEmailContext, comment_label: Optional[str] = None) -> str:
    color = ctx.brand_color or DEFAULT_BRAND_COLOR
    # A region can override with its own hosted logo URL; otherwise use the embedded BRI logo (cid attachment).
    logo_src = ctx.logo_url if ctx.logo_url else f"cid:{LOGO_CONTENT_ID}"
    logo_html = f'<img src="{html_lib.escape(logo_src)}" alt="Blue Rhine Industries" height="32" style="height:32px;display:block;border:0;">'
    rows_html = "".join(_row(label, value) for label, value in rows if value)
    comment_html = ""
    if comment_label and ctx.comment:
        comment_html = f"""<div style="margin-top:16px;padding:12px 14px;background-color:#fff7e6;border-left:3px solid {color};border-radius:4px;">
<p style="margin:0 0 4px 0;font-size:11px;color:#8a6d1f;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;font-family:Arial,Helvetica,sans-serif;">{html_lib.escape(comment_label)}</p>
<p style="margin:0;font-size:13px;color:#4a4a4a;line-height:1.4;font-family:Arial,Helvetica,sans-serif;">{html_lib.escape(ctx.comment)}</p>
</div>"""
    button_html = f"""<table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:20px;">
<tr><td style="border-radius:6px;background-color:{color};">
<a href="{html_lib.escape(_claim_url(ctx.transaction_id))}" style="display:inline-block;padding:10px 22px;font-size:13px;font-weight:600;color:#ffffff;text-decoration:none;font-family:Arial,Helvetica,sans-serif;">View this claim</a>
</td></tr>
</table>"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_lib.escape(heading)}</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f5f7;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;padding:24px 0;">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;font-family:Arial,Helvetica,sans-serif;">
<tr><td style="background-color:{color};padding:18px 24px;">{logo_html}</td></tr>
<tr><td style="padding:24px;">
<h1 style="margin:0 0 8px 0;font-size:18px;color:#1a1a1a;font-family:Arial,Helvetica,sans-serif;">{html_lib.escape(heading)}</h1>
<p style="margin:0 0 20px 0;font-size:14px;color:#444444;line-height:1.5;font-family:Arial,Helvetica,sans-serif;">{html_lib.escape(intro)}</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e4e8;border-radius:6px;">
{rows_html}
</table>
{comment_html}
{button_html}
</td></tr>
<tr><td style="padding:16px 24px;background-color:#f4f5f7;font-size:12px;color:#8a8f98;font-family:Arial,Helvetica,sans-serif;">
This is an automated notification. Please do not reply to this email.
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def _text(heading: str, ctx: ClaimEmailContext, extra: str = "") -> str:
    lines = [
        heading,
        "",
        f"Claim #{ctx.transaction_id} - {ctx.employee_name} - {_truncate(ctx.vendor_name or '-')}",
        f"Total: {_money(ctx.total_amount, ctx.currency)}",
    ]
    if extra:
        lines += ["", extra]
    return "\n".join(lines)


def submission_email(ctx: ClaimEmailContext) -> EmailContent:
    subject = f"Expense claim awaiting your approval - {_money(ctx.total_amount, ctx.currency)}"
    heading = "New expense claim submitted"
    intro = "A new expense claim has been submitted and is awaiting your review."
    html_body = _shell(heading, intro, _common_rows(ctx), ctx)
    text_body = _text(heading, ctx, "This claim is awaiting your review.")
    return EmailContent(subject, html_body, text_body)


def approval_pending_email(ctx: ClaimEmailContext) -> EmailContent:
    subject = f"Expense claim awaiting your approval - {_money(ctx.total_amount, ctx.currency)}"
    heading = "Claim advanced to your approval stage"
    intro = "This expense claim was approved at the previous stage and now needs your review."
    html_body = _shell(heading, intro, _common_rows(ctx), ctx)
    text_body = _text(heading, ctx, "This claim now needs your review.")
    return EmailContent(subject, html_body, text_body)


def approval_final_email(ctx: ClaimEmailContext) -> EmailContent:
    subject = f"Your expense claim was approved - {_money(ctx.total_amount, ctx.currency)}"
    heading = "Expense claim approved"
    intro = "Good news - your expense claim has been fully approved."
    html_body = _shell(heading, intro, _common_rows(ctx), ctx)
    text_body = _text(heading, ctx, "Your claim has been fully approved.")
    return EmailContent(subject, html_body, text_body)


def rejection_email(ctx: ClaimEmailContext) -> EmailContent:
    subject = f"Your expense claim was rejected - {_money(ctx.total_amount, ctx.currency)}"
    heading = "Expense claim rejected"
    intro = "Your expense claim was reviewed and has been rejected."
    html_body = _shell(heading, intro, _common_rows(ctx), ctx, comment_label="Reason for rejection")
    text_body = _text(heading, ctx, f"Reason: {ctx.comment or '-'}")
    return EmailContent(subject, html_body, text_body)


def dispute_email(ctx: ClaimEmailContext) -> EmailContent:
    subject = f"Action needed: correction requested - {_money(ctx.total_amount, ctx.currency)}"
    heading = "Correction needed on your claim"
    intro = "Your expense claim was sent back for correction. Please review the reason below, update your claim, and resubmit."
    html_body = _shell(heading, intro, _common_rows(ctx), ctx, comment_label="Reason for correction request")
    text_body = _text(heading, ctx, f"Reason: {ctx.comment or '-'}")
    return EmailContent(subject, html_body, text_body)


def resubmit_email(ctx: ClaimEmailContext) -> EmailContent:
    subject = f"Corrected claim resubmitted for your approval - {_money(ctx.total_amount, ctx.currency)}"
    heading = "Corrected claim resubmitted"
    intro = "This claim was corrected and resubmitted for your review."
    html_body = _shell(heading, intro, _common_rows(ctx), ctx)
    text_body = _text(heading, ctx, "This claim was corrected and resubmitted for your review.")
    return EmailContent(subject, html_body, text_body)


def paid_email(ctx: ClaimEmailContext) -> EmailContent:
    subject = f"Your expense claim was paid - {_money(ctx.total_amount, ctx.currency)}"
    heading = "Expense claim paid"
    intro = "Your expense claim has been marked as paid."
    html_body = _shell(heading, intro, _common_rows(ctx), ctx, comment_label="Remarks")
    text_body = _text(heading, ctx, f"Remarks: {ctx.comment or '-'}")
    return EmailContent(subject, html_body, text_body)

import html as html_lib
from dataclasses import dataclass
from typing import Optional

from config import get_settings

DEFAULT_BRAND_COLOR = "#1f3a5f"
# Must match services/email_service.py's LOGO_CONTENT_ID -- the cid: the inline attachment is sent under.
LOGO_CONTENT_ID = "bri-logo"

STAGE_LABELS = {
    "hod": "Head of Department",
    "department_hod": "Department HOD",
    "accountant": "Accountant",
    "finance_manager": "Finance Manager",
}

TYPE_LABELS = {
    "reimbursement": "Reimbursement",
    "petty_cash": "Petty Cash",
}

# tone -> (badge background, badge text color, badge label)
TONE_BADGES = {
    "neutral": {"bg": "#eef1f5", "fg": "#45536b", "bg_dark": "#2a2f3a", "fg_dark": "#b7c0d1"},
    "positive": {"bg": "#e6f4ea", "fg": "#1e6b3c", "bg_dark": "#16321f", "fg_dark": "#7fd79b"},
    "dispute": {"bg": "#fff4dd", "fg": "#92400e", "bg_dark": "#3a2c10", "fg_dark": "#f2c572"},
    "rejection": {"bg": "#fdecea", "fg": "#9a3412", "bg_dark": "#3a1f18", "fg_dark": "#f2a58a"},
}

# tone -> comment-callout colors (only dispute/rejection use this)
CALLOUT_COLORS = {
    "dispute": {"bg": "#fff8e6", "border": "#f0b429", "label": "#8a6d1f", "bg_dark": "#2a2110", "border_dark": "#caa53e", "label_dark": "#f2c572"},
    "rejection": {"bg": "#fdf2f0", "border": "#d97757", "label": "#9a3412", "bg_dark": "#2e1c17", "border_dark": "#b25b3f", "label_dark": "#f2a58a"},
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
    expense_type: Optional[str] = None
    project_name: Optional[str] = None
    op_number: Optional[str] = None


@dataclass
class EmailContent:
    subject: str
    html: str
    text: str


def build_context(txn, comment: Optional[str] = None, approver=None) -> ClaimEmailContext:
    region = txn.region
    employee = txn.employee
    project = getattr(txn, "project", None)
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
        expense_type=TYPE_LABELS.get(txn.type, txn.type),
        project_name=project.project_name if project else None,
        op_number=txn.op_number,
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


_ARABIC_RANGES = (("؀", "ۿ"), ("ݐ", "ݿ"), ("ࢠ", "ࣿ"))


def _is_rtl(text: str) -> bool:
    return any(any(lo <= ch <= hi for lo, hi in _ARABIC_RANGES) for ch in text)


def _bidi_value(text: str) -> str:
    escaped = html_lib.escape(text)
    if _is_rtl(text):
        return f'<span dir="rtl" style="unicode-bidi:isolate;">{escaped}</span>'
    return escaped


def _current_holder_row(ctx: ClaimEmailContext) -> Optional[tuple[str, str]]:
    stage_label = _stage_label(ctx.stage)
    if not stage_label:
        return None
    value = f"{ctx.approver_name} ({stage_label})" if ctx.approver_name else stage_label
    return ("Currently with", value)


def _common_rows(ctx: ClaimEmailContext) -> list[tuple[str, Optional[str], str]]:
    # (label, value, variant) -- variant is "default" | "money" | "total"
    rows: list[tuple[str, Optional[str], str]] = [
        ("Claim reference", f"#{ctx.transaction_id}", "default"),
        ("Submitted by", ctx.employee_name or "-", "default"),
        ("Department", ctx.employee_department, "default"),
        ("Submitted on", ctx.submitted_on, "default"),
        ("Vendor", _truncate(ctx.vendor_name or "-"), "default"),
        ("Expense type", ctx.expense_type, "default"),
        ("Category", ctx.category_name or "-", "default"),
    ]
    if ctx.project_name or ctx.op_number:
        project_value = " / ".join(v for v in (ctx.project_name, ctx.op_number) if v)
        rows.append(("Project / OP number", project_value, "default"))
    rows.append(("Bill date", ctx.bill_date or "Not detected", "default"))
    rows.append(("Amount (excl. VAT)", _money(ctx.amount, ctx.currency), "money"))
    rows.append(("VAT amount", _money(ctx.vat_amount, ctx.currency), "money"))
    rows.append(("Total amount", _money(ctx.total_amount, ctx.currency), "total"))
    holder_row = _current_holder_row(ctx)
    if holder_row:
        rows.append((holder_row[0], holder_row[1], "default"))
    return rows


def _row(label: str, value: str, variant: str) -> str:
    label_html = html_lib.escape(label)
    value_html = _bidi_value(value)
    align = "text-align:right;" if variant in ("money", "total") else ""
    if variant == "total":
        return f"""<tr class="bg-total">
<td style="padding:8px 14px;border-top:1px solid #dde1e7;font-size:13px;color:#45536b;width:40%;font-family:Arial,Helvetica,sans-serif;font-weight:600;background-color:#f3f4f6;" class="text-secondary bg-total border-soft">{label_html}</td>
<td style="padding:8px 14px;border-top:1px solid #dde1e7;font-size:15px;color:#111827;font-weight:700;font-family:Arial,Helvetica,sans-serif;{align}word-break:break-word;background-color:#f3f4f6;" class="text-heading bg-total border-soft">{value_html}</td>
</tr>"""
    return f"""<tr>
<td style="padding:7px 14px;border-bottom:1px solid #eef0f3;font-size:13px;color:#6b7280;width:40%;font-family:Arial,Helvetica,sans-serif;" class="text-secondary border-soft">{label_html}</td>
<td style="padding:7px 14px;border-bottom:1px solid #eef0f3;font-size:13px;color:#1a1a1a;font-weight:600;font-family:Arial,Helvetica,sans-serif;{align}word-break:break-word;overflow-wrap:break-word;" class="text-heading border-soft">{value_html}</td>
</tr>"""


_DARK_STYLE_BLOCK = """<style>
@media (prefers-color-scheme: dark) {
  .bg-page { background-color:#121212 !important; }
  .bg-card { background-color:#1e1e1e !important; }
  .bg-total { background-color:#262626 !important; }
  .text-heading { color:#eaeaea !important; }
  .text-body { color:#c9c9c9 !important; }
  .text-secondary { color:#9aa1ac !important; }
  .border-soft { border-color:#33363b !important; }
  .footer-bg { background-color:#171717 !important; color:#7d838c !important; }
}
</style>"""


def _badge_html(tone: str, dark: bool = False) -> str:
    colors = TONE_BADGES[tone]
    bg = colors["bg_dark"] if dark else colors["bg"]
    fg = colors["fg_dark"] if dark else colors["fg"]
    label = {"neutral": "IN PROGRESS", "positive": "APPROVED", "dispute": "ACTION NEEDED", "rejection": "REJECTED"}[tone]
    return f"""<span style="display:inline-block;padding:3px 10px;border-radius:10px;font-size:11px;font-weight:700;letter-spacing:0.4px;background-color:{bg};color:{fg};font-family:Arial,Helvetica,sans-serif;">{label}</span>"""


def _callout_html(tone: str, comment_label: str, comment: Optional[str], dark: bool = False) -> str:
    if not comment:
        return ""
    colors = CALLOUT_COLORS.get(tone, CALLOUT_COLORS["dispute"])
    bg = colors["bg_dark"] if dark else colors["bg"]
    border = colors["border_dark"] if dark else colors["border"]
    label_color = colors["label_dark"] if dark else colors["label"]
    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:16px;">
<tr><td style="padding:12px 14px;background-color:{bg};border-left:3px solid {border};border-radius:4px;">
<p style="margin:0 0 4px 0;font-size:11px;color:{label_color};font-weight:700;text-transform:uppercase;letter-spacing:0.5px;font-family:Arial,Helvetica,sans-serif;">{html_lib.escape(comment_label)}</p>
<p style="margin:0;font-size:13px;color:#4a4a4a;line-height:1.5;font-family:Arial,Helvetica,sans-serif;">{_bidi_value(comment)}</p>
</td></tr>
</table>"""


def _shell(
    heading: str,
    intro: str,
    rows: list[tuple[str, Optional[str], str]],
    ctx: ClaimEmailContext,
    tone: str = "neutral",
    comment_label: Optional[str] = None,
    _force_dark_preview: bool = False,
) -> str:
    color = ctx.brand_color or DEFAULT_BRAND_COLOR
    # A region can override with its own hosted logo URL; otherwise use the embedded BRI logo (cid attachment).
    logo_src = ctx.logo_url if ctx.logo_url else f"cid:{LOGO_CONTENT_ID}"
    logo_html = f'<img src="{html_lib.escape(logo_src)}" alt="Blue Rhine Industries" height="40" style="height:40px;display:block;border:0;">'
    rows_html = "".join(_row(label, value, variant) for label, value, variant in rows if value)
    callout_html = _callout_html(tone, comment_label, ctx.comment, dark=_force_dark_preview) if comment_label else ""
    badge_html = _badge_html(tone, dark=_force_dark_preview)
    button_html = f"""<table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:20px;">
<tr><td style="border-radius:6px;background-color:{color};">
<a href="{html_lib.escape(_claim_url(ctx.transaction_id))}" style="display:inline-block;padding:10px 22px;font-size:13px;font-weight:600;color:#ffffff;text-decoration:none;font-family:Arial,Helvetica,sans-serif;">View this claim</a>
</td></tr>
</table>"""
    # _force_dark_preview bakes the dark palette in directly (for offline preview rendering only) --
    # the real, shipped emails rely on the <style> block's @media query instead, since that is what
    # actual dark-mode-aware clients (Apple Mail, Gmail app, new Outlook) honor at render time.
    if _force_dark_preview:
        page_bg, card_bg, total_bg = "#121212", "#1e1e1e", "#262626"
        text_heading, text_secondary, border_soft = "#eaeaea", "#9aa1ac", "#33363b"
        footer_bg, footer_text = "#171717", "#7d838c"
        rows_html = (
            rows_html.replace("#f3f4f6", total_bg)
            .replace("#eef0f3", border_soft)
            .replace("#dde1e7", border_soft)
            .replace("#6b7280", text_secondary)
            .replace("#1a1a1a", text_heading)
            .replace("#111827", text_heading)
            .replace("#45536b", text_secondary)
        )
        style_block = ""
    else:
        page_bg, card_bg = "#f4f5f7", "#ffffff"
        text_heading, text_secondary = "#1a1a1a", "#444444"
        footer_bg, footer_text = "#f4f5f7", "#8a8f98"
        style_block = _DARK_STYLE_BLOCK
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<title>{html_lib.escape(heading)}</title>
{style_block}
</head>
<body class="bg-page" style="margin:0;padding:0;background-color:{page_bg};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{page_bg}" class="bg-page" style="background-color:{page_bg};padding:24px 0;">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" bgcolor="{card_bg}" class="bg-card" style="background-color:{card_bg};border-radius:8px;overflow:hidden;font-family:Arial,Helvetica,sans-serif;max-width:600px;">
<tr><td style="background-color:{color};padding:22px 24px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td style="vertical-align:middle;">{logo_html}</td>
<td style="vertical-align:middle;text-align:right;color:#dbe4f0;font-size:12px;font-family:Arial,Helvetica,sans-serif;letter-spacing:0.3px;">Petty Cash &amp; Expense</td>
</tr></table>
</td></tr>
<tr><td style="padding:24px;">
<div style="margin-bottom:10px;">{badge_html}</div>
<h1 class="text-heading" style="margin:0 0 8px 0;font-size:18px;color:{text_heading};font-family:Arial,Helvetica,sans-serif;">{html_lib.escape(heading)}</h1>
<p class="text-body" style="margin:0 0 20px 0;font-size:14px;color:{text_secondary};line-height:1.5;font-family:Arial,Helvetica,sans-serif;">{html_lib.escape(intro)}</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" class="border-soft" style="border:1px solid #e2e4e8;border-radius:6px;">
{rows_html}
</table>
{callout_html}
{button_html}
</td></tr>
<tr><td class="footer-bg" style="padding:16px 24px;background-color:{footer_bg};font-size:12px;color:{footer_text};font-family:Arial,Helvetica,sans-serif;">
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


def submission_email(ctx: ClaimEmailContext, _force_dark_preview: bool = False) -> EmailContent:
    subject = f"Expense claim awaiting your approval - {_money(ctx.total_amount, ctx.currency)}"
    heading = "New expense claim submitted"
    intro = "A new expense claim has been submitted and is awaiting your review."
    html_body = _shell(heading, intro, _common_rows(ctx), ctx, tone="neutral", _force_dark_preview=_force_dark_preview)
    text_body = _text(heading, ctx, "This claim is awaiting your review.")
    return EmailContent(subject, html_body, text_body)


def approval_pending_email(ctx: ClaimEmailContext, _force_dark_preview: bool = False) -> EmailContent:
    subject = f"Expense claim awaiting your approval - {_money(ctx.total_amount, ctx.currency)}"
    heading = "Claim advanced to your approval stage"
    intro = "This expense claim was approved at the previous stage and now needs your review."
    html_body = _shell(heading, intro, _common_rows(ctx), ctx, tone="neutral", _force_dark_preview=_force_dark_preview)
    text_body = _text(heading, ctx, "This claim now needs your review.")
    return EmailContent(subject, html_body, text_body)


def approval_final_email(ctx: ClaimEmailContext, _force_dark_preview: bool = False) -> EmailContent:
    subject = f"Your expense claim was approved - {_money(ctx.total_amount, ctx.currency)}"
    heading = "Expense claim approved"
    intro = "Good news - your expense claim has been fully approved."
    html_body = _shell(heading, intro, _common_rows(ctx), ctx, tone="positive", _force_dark_preview=_force_dark_preview)
    text_body = _text(heading, ctx, "Your claim has been fully approved.")
    return EmailContent(subject, html_body, text_body)


def rejection_email(ctx: ClaimEmailContext, _force_dark_preview: bool = False) -> EmailContent:
    subject = f"Your expense claim was rejected - {_money(ctx.total_amount, ctx.currency)}"
    heading = "Expense claim rejected"
    intro = "Your expense claim was reviewed and has been rejected."
    html_body = _shell(
        heading, intro, _common_rows(ctx), ctx, tone="rejection", comment_label="Reason for rejection", _force_dark_preview=_force_dark_preview
    )
    text_body = _text(heading, ctx, f"Reason: {ctx.comment or '-'}")
    return EmailContent(subject, html_body, text_body)


def dispute_email(ctx: ClaimEmailContext, _force_dark_preview: bool = False) -> EmailContent:
    subject = f"Action needed: correction requested - {_money(ctx.total_amount, ctx.currency)}"
    heading = "Correction needed on your claim"
    intro = "Your expense claim was sent back for correction. Please review the reason below, update your claim, and resubmit."
    html_body = _shell(
        heading, intro, _common_rows(ctx), ctx, tone="dispute", comment_label="Reason for correction request", _force_dark_preview=_force_dark_preview
    )
    text_body = _text(heading, ctx, f"Reason: {ctx.comment or '-'}")
    return EmailContent(subject, html_body, text_body)


def resubmit_email(ctx: ClaimEmailContext, _force_dark_preview: bool = False) -> EmailContent:
    subject = f"Corrected claim resubmitted for your approval - {_money(ctx.total_amount, ctx.currency)}"
    heading = "Corrected claim resubmitted"
    intro = "This claim was corrected and resubmitted for your review."
    html_body = _shell(heading, intro, _common_rows(ctx), ctx, tone="neutral", _force_dark_preview=_force_dark_preview)
    text_body = _text(heading, ctx, "This claim was corrected and resubmitted for your review.")
    return EmailContent(subject, html_body, text_body)


def paid_email(ctx: ClaimEmailContext, _force_dark_preview: bool = False) -> EmailContent:
    subject = f"Your expense claim was paid - {_money(ctx.total_amount, ctx.currency)}"
    heading = "Expense claim paid"
    intro = "Your expense claim has been marked as paid."
    html_body = _shell(
        heading, intro, _common_rows(ctx), ctx, tone="positive", comment_label="Remarks", _force_dark_preview=_force_dark_preview
    )
    text_body = _text(heading, ctx, f"Remarks: {ctx.comment or '-'}")
    return EmailContent(subject, html_body, text_body)

import json

from sqlalchemy.dialects import mssql

from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseApprovalHistory,
    ErpExpenseCategory,
    ErpExpenseNotification,
    ErpExpenseRegionConfig,
    ErpExpenseTransaction,
    ErpExpenseVendor,
)
from services import email_templates as et

KSA_VENDOR = "شركة قمة الخليج المحدودة للأجرة العامة"


def _ctx(**overrides):
    base = dict(
        transaction_id=26,
        employee_name="Fatima Al Suwaidi",
        vendor_name=KSA_VENDOR,
        amount=20.0,
        vat_amount=1.0,
        total_amount=21.0,
        currency="AED",
        bill_date="2026-08-18",
        category_name="Transport",
        stage="hod",
    )
    base.update(overrides)
    return et.ClaimEmailContext(**base)


def test_subject_leads_with_action_and_amount_not_vendor():
    content = et.submission_email(_ctx())
    assert "AED 21.00" in content.subject
    assert KSA_VENDOR not in content.subject


def test_amounts_formatted_to_two_decimals_with_currency():
    content = et.submission_email(_ctx(amount=20, vat_amount=1, total_amount=21))
    assert "AED 20.00" in content.html
    assert "AED 1.00" in content.html
    assert "AED 21.00" in content.html


def test_arabic_vendor_name_renders_intact_in_html_and_text():
    content = et.submission_email(_ctx())
    assert KSA_VENDOR in content.html
    assert KSA_VENDOR in content.text


def test_long_vendor_name_truncated_only_in_body_not_subject():
    long_name = "A" * 120
    content = et.submission_email(_ctx(vendor_name=long_name))
    assert long_name not in content.html  # truncated with an ellipsis
    assert "…" in content.html
    assert long_name not in content.subject


def test_comment_block_present_only_when_comment_given():
    without = et.submission_email(_ctx())
    assert "Reason" not in without.html
    with_comment = et.rejection_email(_ctx(comment="Missing invoice"))
    assert "Reason for rejection" in with_comment.html
    assert "Missing invoice" in with_comment.html


def test_dispute_and_rejection_have_distinct_wording():
    rejection = et.rejection_email(_ctx(comment="x"))
    dispute = et.dispute_email(_ctx(comment="x"))
    assert rejection.subject != dispute.subject
    assert rejection.html != dispute.html


def test_html_declares_utf8_charset():
    content = et.submission_email(_ctx())
    assert '<meta charset="utf-8">' in content.html


def test_no_default_branding_falls_back_to_embedded_logo_only():
    content = et.submission_email(_ctx())
    assert f'cid:{et.LOGO_CONTENT_ID}' in content.html
    assert et.DEFAULT_BRAND_COLOR in content.html
    assert "Expense Receipt App" not in content.html  # no text app/company name anywhere


def test_region_logo_url_overrides_the_embedded_logo():
    content = et.submission_email(_ctx(logo_url="https://example.com/logo.png"))
    assert "https://example.com/logo.png" in content.html
    assert f'cid:{et.LOGO_CONTENT_ID}' not in content.html


def test_stage_row_omitted_when_stage_is_none():
    content = et.approval_final_email(_ctx(stage=None))
    assert "Current stage" not in content.html


def test_submitted_by_department_and_submitted_on_shown():
    content = et.submission_email(_ctx(employee_department="Sales", submitted_on="18 Aug 2026, 14:32"))
    assert "Submitted by" in content.html
    assert "Sales" in content.html
    assert "18 Aug 2026, 14:32" in content.html


def test_current_holder_row_shows_stage_alone_or_name_and_stage():
    without_name = et.submission_email(_ctx())
    assert "Currently with" in without_name.html
    assert "Head of Department" in without_name.html  # stage label, resolved from stage="hod"
    with_approver = et.submission_email(_ctx(approver_name="Ali Hassan"))
    assert "Currently with" in with_approver.html
    assert "Ali Hassan" in with_approver.html
    assert "Head of Department" in with_approver.html


def test_current_holder_row_absent_once_stage_is_cleared():
    no_stage = et.submission_email(_ctx(stage=None))
    assert "Currently with" not in no_stage.html


def test_view_claim_button_links_to_the_public_base_url():
    content = et.submission_email(_ctx())
    assert "View this claim" in content.html
    assert "/claims/26" in content.html


def test_unicode_round_trip_through_graph_json_payload():
    content = et.submission_email(_ctx())
    payload = {"message": {"subject": content.subject, "body": {"contentType": "HTML", "content": content.html}}}
    raw = json.dumps(payload).encode("utf-8")
    decoded = json.loads(raw.decode("utf-8"))
    assert KSA_VENDOR in decoded["message"]["body"]["content"]


def _mssql_ddl_type(column) -> str:
    return column.type.compile(dialect=mssql.dialect())


def test_email_path_columns_compile_to_unicode_types_on_mssql():
    unicode_columns = [
        ErpExpenseVendor.__table__.c.vendorName,
        ErpAuthExpenseUsers.__table__.c.displayName,
        ErpExpenseCategory.__table__.c.categoryName,
        ErpExpenseCategory.__table__.c.categoryNameAr,
        ErpExpenseTransaction.__table__.c.remarks,
        ErpExpenseApprovalHistory.__table__.c.comment,
        ErpExpenseRegionConfig.__table__.c.companyName,
        ErpExpenseNotification.__table__.c.message,
    ]
    for column in unicode_columns:
        ddl_type = _mssql_ddl_type(column).upper()
        assert ddl_type.startswith(("NVARCHAR", "NTEXT")), f"{column} compiles to {ddl_type}, not Unicode-safe"

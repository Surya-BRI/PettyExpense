"""End-to-end smoke test for Phase 1 + Phase 2: submit an IT-Equipment claim as the
Sales employee, confirm it routes hod -> department_hod -> accountant -> finance_manager,
walk it through all 4 approvals, then mark it paid.

Run from backend/ with uvicorn already running on :8000.
"""
import httpx
from pathlib import Path

base = "http://127.0.0.1:8000"


def call(method, url, data=None, files=None, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if files:
        r = httpx.request(method, url, files=files, headers=headers, timeout=30)
    else:
        r = httpx.request(method, url, json=data, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


def login(username, password):
    return call("POST", f"{base}/api/auth/login", {"username": username, "password": password})["access_token"]


employee_token = login("surya", "surya123")
admin_token = login("teja", "teja123")
hod_token = login("sajeesh", "sajeesh123")
it_hod_token = login("denny", "denny123")
accountant_token = login("anjana", "anjana123")
finance_token = login("sandeep", "sandeep123")

categories = call("GET", f"{base}/api/admin/config/categories", token=admin_token)
it_category = next(c for c in categories if c["name"] == "IT Equipment")
print("category", it_category)

uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(exist_ok=True)
existing_jpgs = list(uploads_dir.glob("*.jpg"))
img_bytes = existing_jpgs[0].read_bytes() if existing_jpgs else b"\xff\xd8\xff\xd9"

ocr = call(
    "POST",
    f"{base}/api/claims/ocr",
    files={"file": ("e2e.jpg", img_bytes, "image/jpeg")},
    token=employee_token,
)
print("ocr", ocr["receipt_id"], ocr["vendor"])

claim = call(
    "POST",
    f"{base}/api/claims",
    {
        "vendor": "Tech Bazaar Electronics",
        "amount": ocr["amount"] or 1200,
        "bill_date": ocr["date"] or "2026-08-01",
        "category_id": it_category["id"],
        "region_code": "IN",
        "type": "reimbursement",
        "receipt_id": ocr["receipt_id"],
        "s3_key": ocr["s3_key"],
        "submit": True,
    },
    token=employee_token,
)
claim_id = claim["id"]
print("claim", claim_id, claim["status"])

print("hod queue:", [t["id"] for t in call("GET", f"{base}/api/approvals/queue?stage=hod", token=hod_token)])
step1 = call("POST", f"{base}/api/approvals/{claim_id}/approve", {"comment": "sales hod ok"}, token=hod_token)
print("after hod approve -> current_stage:", step1["current_stage"], "status:", step1["status"])

print("dept-hod queue:", [t["id"] for t in call("GET", f"{base}/api/approvals/queue?stage=department_hod", token=it_hod_token)])
step2 = call("POST", f"{base}/api/approvals/{claim_id}/approve", {"comment": "it hod ok"}, token=it_hod_token)
print("after dept hod approve -> current_stage:", step2["current_stage"], "status:", step2["status"])

step3 = call("POST", f"{base}/api/approvals/{claim_id}/approve", {"comment": "accountant ok"}, token=accountant_token)
print("after accountant approve -> current_stage:", step3["current_stage"], "status:", step3["status"])

step4 = call("POST", f"{base}/api/approvals/{claim_id}/approve", {"comment": "fm ok"}, token=finance_token)
print("after finance_manager approve -> status:", step4["status"])

paid = call("POST", f"{base}/api/admin/claims/{claim_id}/mark-paid", {"remarks": "neft done"}, token=finance_token)
print("paid", paid["status"])

detail = call("GET", f"{base}/api/claims/{claim_id}", token=employee_token)
print("history stages:", [(h["stage"], h["action"]) for h in detail["history"]])

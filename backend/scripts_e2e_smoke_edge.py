"""Edge-case smoke test: dispute-return-to-stage, reject-is-terminal,
same-person auto-skip, bulk-approve. Run with uvicorn already running on :8000."""
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
accountant_token = login("anjana", "anjana123")
finance_token = login("sandeep", "sandeep123")
hod_user_id = call("GET", f"{base}/api/auth/me", token=hod_token)["id"]

categories = call("GET", f"{base}/api/admin/config/categories", token=admin_token)
food_category = next(c for c in categories if c["name"] == "Food")

uploads_dir = Path(__file__).parent / "uploads"
img_bytes = b"\xff\xd8\xff\xd9"


def submit_claim(vendor, amount, bill_date):
    ocr = call("POST", f"{base}/api/claims/ocr", files={"file": ("e.jpg", img_bytes, "image/jpeg")}, token=employee_token)
    return call(
        "POST",
        f"{base}/api/claims",
        {
            "vendor": vendor,
            "amount": amount,
            "bill_date": bill_date,
            "category_id": food_category["id"],
            "region_code": "IN",
            "receipt_id": ocr["receipt_id"],
            "s3_key": ocr["s3_key"],
            "submit": True,
        },
        token=employee_token,
    )


# --- Test 1: dispute at accountant stage returns to accountant, not hod, on resubmit ---
print("=== Test 1: dispute-return-to-stage ===")
c1 = submit_claim("City Mart Supplies", 50, "2026-08-02")
call("POST", f"{base}/api/approvals/{c1['id']}/approve", {"comment": "ok"}, token=hod_token)
disputed = call("POST", f"{base}/api/approvals/{c1['id']}/dispute", {"comment": "wrong amount, please fix"}, token=accountant_token)
print("after dispute -> status:", disputed["status"], "current_stage:", disputed["current_stage"], "dispute_returned:", disputed["dispute_returned"])
resubmitted = call("POST", f"{base}/api/claims/{c1['id']}/resubmit", token=employee_token)
print("after resubmit -> status:", resubmitted["status"], "current_stage:", resubmitted["current_stage"], "(expect: submitted / accountant)")
assert resubmitted["status"] == "submitted" and resubmitted["current_stage"] == "accountant", "FAIL: dispute-return broken"
print("PASS")

# --- Test 2: reject is terminal, further approve attempts fail ---
print("\n=== Test 2: reject-is-terminal ===")
c2 = submit_claim("City Mart Supplies", 60, "2026-08-03")
call("POST", f"{base}/api/approvals/{c2['id']}/approve", {"comment": "ok"}, token=hod_token)
rejected = call("POST", f"{base}/api/approvals/{c2['id']}/reject", {"comment": "not a valid expense"}, token=accountant_token)
print("after reject -> status:", rejected["status"])
try:
    call("POST", f"{base}/api/approvals/{c2['id']}/approve", {"comment": "too late"}, token=finance_token)
    print("FAIL: approve succeeded on a rejected transaction")
except httpx.HTTPStatusError as exc:
    print(f"PASS: further approve correctly rejected with {exc.response.status_code}")

# --- Test 3: same-person auto-skip. Isolated in a brand-new department so there's no
# ambiguity from IT already having its own HOD (denny) — 'sajeesh' becomes the ONLY HOD of
# the new "Legal" department too, so category.owning_department_id != employee.department_id
# (Sales != Legal) but the resolved approver for both stages is the same person.
print("\n=== Test 3: same-person auto-skip ===")
legal_dept = call("POST", f"{base}/api/admin/config/departments", {"name": "Legal"}, token=admin_token)
call("POST", f"{base}/api/admin/config/hod-assignments", {"user_id": hod_user_id, "department_id": legal_dept["id"]}, token=admin_token)
legal_category = call(
    "POST", f"{base}/api/admin/config/categories", {"name": "Legal Fees", "owning_department_id": legal_dept["id"]}, token=admin_token
)
ocr = call("POST", f"{base}/api/claims/ocr", files={"file": ("e.jpg", img_bytes, "image/jpeg")}, token=employee_token)
c3 = call(
    "POST",
    f"{base}/api/claims",
    {
        "vendor": "Tech Bazaar Electronics",
        "amount": 75,
        "bill_date": "2026-08-04",
        "category_id": legal_category["id"],
        "region_code": "IN",
        "receipt_id": ocr["receipt_id"],
        "s3_key": ocr["s3_key"],
        "submit": True,
    },
    token=employee_token,
)
step = call("POST", f"{base}/api/approvals/{c3['id']}/approve", {"comment": "sales hod (also legal hod) ok"}, token=hod_token)
print("after hod approve -> current_stage:", step["current_stage"], "(expect: accountant, department_hod skipped)")
assert step["current_stage"] == "accountant", "FAIL: department_hod stage was not skipped"
print("PASS")

# --- Test 4: bulk-approve ---
print("\n=== Test 4: bulk-approve ===")
c4 = submit_claim("City Mart Supplies", 30, "2026-08-05")
c5 = submit_claim("City Mart Supplies", 30, "2026-08-06")
bulk = call("POST", f"{base}/api/approvals/bulk-approve", {"transaction_ids": [c4["id"], c5["id"]]}, token=hod_token)
print("bulk result:", bulk)
assert set(bulk["approved"]) == {c4["id"], c5["id"]}, "FAIL: bulk-approve did not approve both"
print("PASS")

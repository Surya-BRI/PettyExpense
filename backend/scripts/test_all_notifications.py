"""Drives one claim through every lifecycle stage against the local running backend,
firing all real notification types in sequence for manual inbox comparison.

Run from backend/ with uvicorn already running on BASE_URL (see below).
Every user in ErpAuthExpenseUsers has email=aiengineer@brisigns.com in this DB,
so every email lands in one inbox.

Uses assets/dubai/enoc_test.jpg and assets/ksa/ksa2.png so the emails carry real
OCR output. Both images are uploaded via /api/claims/ocr, which stores the photo
through the currently configured STORAGE_BACKEND (see the note printed at startup).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import httpx

BASE_URL = "http://localhost:8000"
BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent
ASSETS = REPO_ROOT / "assets"

sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_ROOT / ".env")

from config import get_settings  # noqa: E402
from database.models import ErpAuthExpenseUsers, ErpExpenseNotification, SessionLocal  # noqa: E402

PASSWORDS = {
    "surya": "surya123",
    "sajeesh": "sajeesh123",
    "anjana": "anjana123",
    "sandeep": "sandeep123",
}

results = []


def call(method, path, token=None, json_body=None, files=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{BASE_URL}{path}"
    if files:
        return httpx.request(method, url, files=files, headers=headers, timeout=60)
    return httpx.request(method, url, json=json_body, headers=headers, timeout=60)


def login(username):
    resp = call("POST", "/api/auth/login", json_body={"username": username, "password": PASSWORDS[username]})
    resp.raise_for_status()
    return resp.json()["access_token"]


def max_notification_id(db):
    row = db.query(ErpExpenseNotification).order_by(ErpExpenseNotification.notification_id.desc()).first()
    return row.notification_id if row else 0


def new_rows_since(db, since_id):
    return (
        db.query(ErpExpenseNotification)
        .filter(ErpExpenseNotification.notification_id > since_id)
        .order_by(ErpExpenseNotification.notification_id.asc())
        .all()
    )


def username_for(db, user_id):
    user = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == user_id).first()
    return user.user_name if user else f"user#{user_id}"


def run_step(step_name, expected_recipient, action):
    db = SessionLocal()
    try:
        before_id = max_notification_id(db)
        print(f"\n=== {step_name} ===")
        print(f"Expected recipient: {expected_recipient}")
        try:
            status_code = action()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            print(f"HTTP status: {status_code} (error body: {exc.response.text[:300]})")
            results.append(
                {"step": step_name, "http_status": status_code, "expected": expected_recipient, "email_status": "CALL_FAILED", "note": exc.response.text[:120]}
            )
            return
        print(f"HTTP status: {status_code}")
        db.expire_all()
        new_rows = new_rows_since(db, before_id)
        email_rows = [r for r in new_rows if r.channel == "email"]
        if not new_rows:
            print("NO NOTIFICATION ROW CREATED (likely swallowed by idempotency dedup, or the call produced no notify() call)")
            results.append(
                {"step": step_name, "http_status": status_code, "expected": expected_recipient, "email_status": "NONE", "note": "no row at all"}
            )
        else:
            for row in new_rows:
                who = username_for(db, row.user_id)
                print(f"row: type={row.type} channel={row.channel} status={row.status} to={who}")
            email_status = email_rows[0].status if email_rows else "NO_EMAIL_ROW"
            results.append(
                {"step": step_name, "http_status": status_code, "expected": expected_recipient, "email_status": email_status, "note": ""}
            )
    finally:
        db.close()


def get_food_category_id(token):
    resp = call("GET", "/api/categories", token=token)
    resp.raise_for_status()
    food = next(c for c in resp.json() if c["name"] == "Food")
    return food["id"]


def submit_claim(token, image_path, region_code, category_id):
    files = {"file": (image_path.name, image_path.read_bytes(), "image/jpeg")}
    ocr_resp = call("POST", "/api/claims/ocr", token=token, files=files)
    ocr_resp.raise_for_status()
    ocr = ocr_resp.json()
    claim_resp = call(
        "POST",
        "/api/claims",
        token=token,
        json_body={
            "vendor": ocr["vendor"] or "Unknown vendor",
            "amount": ocr["amount"] or 1.0,
            "vat_amount": ocr["vat_amount"] or 0.0,
            "total_amount": ocr["total_amount"],
            "currency": ocr["currency"] or "AED",
            "bill_date": ocr["date"] or None,
            "category_id": category_id,
            "region_code": region_code,
            "type": "reimbursement",
            "receipt_id": ocr["receipt_id"],
            "s3_key": ocr["s3_key"],
            "submit": True,
        },
    )
    claim_resp.raise_for_status()
    return claim_resp.json()["id"], ocr, claim_resp.status_code


def main():
    settings = get_settings()
    print(f"STORAGE_BACKEND={settings.storage_backend} bucket={settings.bucket_name}")
    print(f"NOTIFY_EMAIL_ENABLED={settings.notify_email_enabled}")

    surya = login("surya")
    sajeesh = login("sajeesh")
    anjana = login("anjana")
    sandeep = login("sandeep")

    category_id = get_food_category_id(surya)

    claim1_id = {}

    def step1():
        cid, ocr, status_code = submit_claim(surya, ASSETS / "dubai" / "enoc_test.jpg", "UAE", category_id)
        claim1_id["id"] = cid
        print(f"claim1 id={cid} vendor={ocr['vendor']} amount={ocr['amount']}")
        return status_code

    run_step("1. surya submits claim1 (submission -> hod)", "sajeesh (hod)", step1)

    def step2():
        resp = call("POST", f"/api/approvals/{claim1_id['id']}/dispute", token=sajeesh, json_body={"comment": "Missing itemized breakdown, please resubmit."})
        resp.raise_for_status()
        return resp.status_code

    run_step("2. sajeesh disputes claim1 (dispute -> employee)", "surya (employee)", step2)

    def step3():
        resp = call("POST", f"/api/claims/{claim1_id['id']}/resubmit", token=surya)
        resp.raise_for_status()
        return resp.status_code

    run_step("3. surya resubmits claim1 (resubmit -> disputing approver)", "sajeesh (hod, same stage as dispute)", step3)

    def step4():
        resp = call("POST", f"/api/approvals/{claim1_id['id']}/approve", token=sajeesh, json_body={"comment": "Looks correct now."})
        resp.raise_for_status()
        return resp.status_code

    run_step("4. sajeesh approves claim1 (approval -> accountant)", "anjana (accountant)", step4)

    def step5():
        resp = call("POST", f"/api/approvals/{claim1_id['id']}/approve", token=anjana, json_body={"comment": "Verified."})
        resp.raise_for_status()
        return resp.status_code

    run_step("5. anjana approves claim1 (approval -> finance manager)", "sandeep (finance_manager)", step5)

    def step6():
        resp = call("POST", f"/api/approvals/{claim1_id['id']}/approve", token=sandeep, json_body={"comment": "Final approval."})
        resp.raise_for_status()
        return resp.status_code

    run_step("6. sandeep approves claim1 (final approval -> employee)", "surya (employee)", step6)

    def step7():
        resp = call("POST", f"/api/admin/claims/{claim1_id['id']}/mark-paid", token=sandeep, json_body={"remarks": "Bank transfer done."})
        resp.raise_for_status()
        return resp.status_code

    run_step("7. sandeep marks claim1 paid (paid -> employee)", "surya (employee)", step7)

    claim2_id = {}

    def step8a():
        cid, ocr, status_code = submit_claim(surya, ASSETS / "ksa" / "ksa2.png", "KSA", category_id)
        claim2_id["id"] = cid
        print(f"claim2 id={cid} vendor={ocr['vendor']} amount={ocr['amount']}")
        return status_code

    run_step("8a. surya submits claim2 (submission -> hod)", "sajeesh (hod)", step8a)

    def step8b():
        resp = call("POST", f"/api/approvals/{claim2_id['id']}/reject", token=sajeesh, json_body={"comment": "Not a valid business expense."})
        resp.raise_for_status()
        return resp.status_code

    run_step("8b. sajeesh rejects claim2 (rejection -> employee)", "surya (employee)", step8b)

    print("\n\n=== SUMMARY ===")
    header = f"{'step':55} {'http':5} {'expected':30} {'email_status':15}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(f"{r['step']:55} {r['http_status']:<5} {r['expected']:30} {r['email_status']:15} {r['note']}")


if __name__ == "__main__":
    main()

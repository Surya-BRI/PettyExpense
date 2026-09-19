from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["public"])


@router.get("/claims/{transaction_id}", response_class=HTMLResponse)
def claim_fallback_page(transaction_id: int) -> str:
    # Public and unauthenticated by design -- this is the "View this claim" email button target
    # before app-link deep-linking is set up, and will keep serving as the fallback afterwards for
    # anyone without the app installed. It deliberately shows no claim data, just the id, since
    # anyone with the email link (not necessarily the recipient) can load this in a browser.
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Petty Expense - Claim #{transaction_id}</title>
</head>
<body style="margin:0;padding:40px 20px;background-color:#f4f5f7;font-family:Arial,Helvetica,sans-serif;color:#1a1a1a;">
<div style="max-width:420px;margin:0 auto;background:#ffffff;border-radius:10px;padding:32px;text-align:center;">
<h1 style="font-size:18px;margin:0 0 12px 0;">Open claim #{transaction_id} in the app</h1>
<p style="font-size:14px;color:#555555;line-height:1.5;margin:0 0 20px 0;">
This link is for Claim #{transaction_id}. Open the Petty Expense app and sign in to view it &mdash;
opening straight into the app from this link is coming soon.
</p>
</div>
</body>
</html>"""

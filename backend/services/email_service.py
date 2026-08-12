import logging
from typing import Optional

import httpx

from config import get_settings

logger = logging.getLogger("expense.email")


class EmailService:
    def notify(self, to_email: Optional[str], subject: str, body: str) -> bool:
        settings = get_settings()
        if not to_email:
            logger.info("Skip email (no recipient): %s", subject)
            return False

        if not settings.notify_email_enabled:
            logger.info("[STUB EMAIL] to=%s subject=%s body=%s", to_email, subject, body)
            return True

        if not all(
            [
                settings.graph_tenant_id,
                settings.graph_client_id,
                settings.graph_client_secret,
                settings.graph_sender,
            ]
        ):
            logger.warning("Graph email enabled but credentials incomplete; logging stub")
            logger.info("[STUB EMAIL] to=%s subject=%s body=%s", to_email, subject, body)
            return True

        try:
            token = self._graph_token()
            payload = {
                "message": {
                    "subject": subject,
                    "body": {"contentType": "Text", "content": body},
                    "toRecipients": [{"emailAddress": {"address": to_email}}],
                },
                "saveToSentItems": "false",
            }
            url = f"https://graph.microsoft.com/v1.0/users/{settings.graph_sender}/sendMail"
            resp = httpx.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            return True
        except Exception as exc:
            logger.exception("Failed to send Graph email: %s", exc)
            return False

    def _graph_token(self) -> str:
        settings = get_settings()
        token_url = (
            f"https://login.microsoftonline.com/{settings.graph_tenant_id}/oauth2/v2.0/token"
        )
        data = {
            "client_id": settings.graph_client_id,
            "client_secret": settings.graph_client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }
        resp = httpx.post(token_url, data=data, timeout=30)
        resp.raise_for_status()
        return resp.json()["access_token"]


email_service = EmailService()

import hashlib
import logging
import uuid
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config import get_settings

logger = logging.getLogger("expense.storage")


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _s3_client(self):
        return boto3.client(
            "s3",
            region_name=self.settings.aws_region,
            aws_access_key_id=self.settings.aws_access_key_id or None,
            aws_secret_access_key=self.settings.aws_secret_access_key or None,
        )

    def _use_s3(self) -> bool:
        return self.settings.storage_backend == "s3" and bool(self.settings.bucket_name)

    def save_bytes(self, data: bytes, content_type: str = "image/jpeg", ext: str = "jpg") -> str:
        key = f"{self.settings.s3_key_prefix}{uuid.uuid4().hex}.{ext}"

        if self._use_s3():
            self._s3_client().put_object(
                Bucket=self.settings.bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            return key

        # local fallback only when STORAGE_BACKEND != s3
        local_name = Path(key).name
        path = self.settings.upload_path / local_name
        path.write_bytes(data)
        return f"local/{local_name}"

    def read_bytes(self, key: str) -> Optional[bytes]:
        if key.startswith("local/"):
            path = self.settings.upload_path / key.split("/", 1)[1]
            if path.exists():
                return path.read_bytes()
            return None

        if not self.settings.bucket_name:
            return None
        try:
            obj = self._s3_client().get_object(Bucket=self.settings.bucket_name, Key=key)
            return obj["Body"].read()
        except (BotoCoreError, ClientError) as exc:
            logger.warning("S3 get_object failed for %s: %s", key, exc)
            return None

    def presigned_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """Signed GET URL for Flutter / browser preview."""
        if not key or key.startswith("local/") or not self.settings.bucket_name:
            return None
        try:
            return self._s3_client().generate_presigned_url(
                "get_object",
                Params={"Bucket": self.settings.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
        except (BotoCoreError, ClientError) as exc:
            logger.warning("presign failed for %s: %s", key, exc)
            return None

    @staticmethod
    def image_hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()


storage_service = StorageService()

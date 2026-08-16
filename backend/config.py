from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Expense Receipt App"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # ERP Dev SQL Server — only database (auth, claims, everything)
    reader_db_server: str = ""
    reader_db_name: str = ""
    reader_db_user: str = ""
    reader_db_password: str = ""
    reader_db_driver: str = "ODBC Driver 17 for SQL Server"

    # AWS S3 (receipt images + signed URLs)
    storage_backend: str = "s3"  # s3 | local
    local_upload_dir: str = "./uploads"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-south-1"
    aws_bucket: str = ""  # env: AWS_BUCKET
    aws_folder: str = "live"  # env: AWS_FOLDER
    s3_bucket: str = ""  # optional fallback
    s3_prefix: str = ""  # optional extra path under folder

    ocr_backend: str = "paddle"  # paddle | stub

    auth_mode: str = "mock"  # mock | erp
    cors_origins: str = "*"

    graph_tenant_id: str = ""
    graph_client_id: str = ""
    graph_client_secret: str = ""
    graph_sender: str = ""
    notify_email_enabled: bool = False

    @model_validator(mode="after")
    def require_erp_db(self) -> "Settings":
        missing = [
            name
            for name, val in [
                ("READER_DB_SERVER", self.reader_db_server),
                ("READER_DB_NAME", self.reader_db_name),
                ("READER_DB_USER", self.reader_db_user),
                ("READER_DB_PASSWORD", self.reader_db_password),
            ]
            if not (val or "").strip()
        ]
        if missing:
            raise ValueError(
                "ERP Dev SQL Server is required (no local SQLite). "
                f"Set in backend/.env: {', '.join(missing)}"
            )
        return self

    @property
    def bucket_name(self) -> str:
        return (self.aws_bucket or self.s3_bucket or "").strip()

    @property
    def s3_key_prefix(self) -> str:
        folder = (self.aws_folder or "live").strip().strip("/")
        extra = (self.s3_prefix or "expense-receipts").strip().strip("/")
        return f"{folder}/{extra}/"

    @property
    def upload_path(self) -> Path:
        path = Path(self.local_upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def odbc_connect_string(self) -> str:
        return (
            f"DRIVER={{{self.reader_db_driver}}};"
            f"SERVER={self.reader_db_server};"
            f"DATABASE={self.reader_db_name};"
            f"UID={self.reader_db_user};"
            f"PWD={self.reader_db_password};"
            "TrustServerCertificate=yes;"
        )

    @property
    def database_url(self) -> str:
        """Single SQLAlchemy URL — ERP Dev only."""
        user = quote_plus(self.reader_db_user)
        password = quote_plus(self.reader_db_password)
        driver = quote_plus(self.reader_db_driver)
        return (
            f"mssql+pyodbc://{user}:{password}@{self.reader_db_server}/"
            f"{self.reader_db_name}?driver={driver}&TrustServerCertificate=yes"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

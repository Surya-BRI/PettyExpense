from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend package root is importable when run as `uvicorn main:app`
load_dotenv(Path(__file__).resolve().parent / ".env")

from api.routes_admin import router as admin_router
from api.routes_approvals import router as approvals_router
from api.routes_auth import router as auth_router
from api.routes_claims import categories_router, router as claims_router
from api.routes_config import router as config_router
from api.routes_notifications import router as notifications_router
from api.routes_projects import router as projects_router
from auth.security import seed_users
from config import get_settings
from database.models import init_db
from scripts.seed_phase1_reference_data import seed_hod_assignments, seed_reference_data

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(claims_router)
app.include_router(categories_router)
app.include_router(admin_router)
app.include_router(approvals_router)
app.include_router(config_router)
app.include_router(projects_router)
app.include_router(notifications_router)


@app.on_event("startup")
def on_startup() -> None:
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    init_db()
    # Order matters: reference data (roles/departments) before users (needs role/department
    # FKs), users before HOD assignments (needs user ids to exist).
    seed_reference_data()
    seed_users()
    seed_hod_assignments()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "auth_mode": settings.auth_mode,
        "storage_backend": settings.storage_backend,
        "aws_bucket": settings.bucket_name,
        "aws_folder": settings.aws_folder,
        "ocr_backend": settings.ocr_backend,
        "db_server": settings.reader_db_server,
        "db_name": settings.reader_db_name,
        "db": "erp-dev-sqlserver",
    }

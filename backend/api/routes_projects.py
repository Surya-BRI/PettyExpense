from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.security import CurrentUser, get_current_user
from database.models import ErpExpenseProjectCache, get_db

router = APIRouter(prefix="/api", tags=["reference"])


@router.get("/projects")
def list_projects(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    projects = db.query(ErpExpenseProjectCache).all()
    return [
        {"id": p.project_cache_id, "name": p.project_name, "op_number": p.op_number}
        for p in projects
    ]

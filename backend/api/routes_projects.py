from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth.security import CurrentUser, get_current_user
from database.models import ErpExpenseProjectCache, get_db
from services.opportunity_lookup import find_opportunity

router = APIRouter(prefix="/api", tags=["reference"])


@router.get("/projects")
def list_projects(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    projects = db.query(ErpExpenseProjectCache).all()
    return [
        {"id": p.project_cache_id, "name": p.project_name, "op_number": p.op_number}
        for p in projects
    ]


@router.get("/opportunities/search")
def search_opportunity(
    code: str = Query(..., min_length=1),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Look up an opportunity by its salesForceCode from the live ERP table."""
    return find_opportunity(db, code)

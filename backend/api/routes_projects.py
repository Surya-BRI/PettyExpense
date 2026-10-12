from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
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


@router.get("/opportunities/search")
def search_opportunity(
    code: str = Query(..., min_length=1),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Look up an opportunity by its salesForceCode from the live ERP table."""
    row = db.execute(
        text(
            "SELECT mo.salesForceCode, mo.opportunityName, "
            "mb.businessUnitCode, "
            "(me.firstName + ' ' + me.lastName) AS salesPerson "
            "FROM ErpMasterOpportunity mo "
            "LEFT JOIN ErpMasterBusinessUnit mb ON mb.businessUnitId = mo.businessUnitId "
            "LEFT JOIN ErpMasterEmployee me ON me.employeeId = mo.salesRepId "
            "WHERE mo.isActive = 1 AND LTRIM(RTRIM(mo.salesForceCode)) = :code"
        ),
        {"code": code.strip()},
    ).first()

    if not row:
        return None

    return {
        "op_code":      row.salesForceCode,
        "name":         row.opportunityName,
        "bu_code":      row.businessUnitCode,
        "sales_person": row.salesPerson,
    }

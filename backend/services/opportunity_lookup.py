"""Project (opportunity) lookup by OP code in the live ERP table -- shared by the bill screen's
OP code field (GET /api/opportunities/search) and employee advances (one per project)."""
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def normalize_op(code: Optional[str]) -> Optional[str]:
    """OP codes are compared trimmed and case-insensitively; None when blank."""
    value = (code or "").strip().upper()
    return value or None


def find_opportunity(db: Session, code: str) -> Optional[dict[str, Any]]:
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
        "op_code": row.salesForceCode,
        "name": row.opportunityName,
        "bu_code": row.businessUnitCode,
        "sales_person": row.salesPerson,
    }

from sqlalchemy import create_engine, text

from config import get_settings

get_settings.cache_clear()
s = get_settings()
e = create_engine(s.database_url, pool_pre_ping=True)

with e.connect() as c:
    tables = [
        r[0]
        for r in c.execute(
            text(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_TYPE='BASE TABLE' AND (TABLE_NAME LIKE 'ErpExpense%' OR TABLE_NAME LIKE 'ErpAuthExpense%' OR TABLE_NAME LIKE 'ErpMasterExpense%')"
            )
        ).fetchall()
    ]
    print("tables:", tables)
    if "ErpAuthExpenseUsers" in tables:
        rows = c.execute(
            text(
                'SELECT u."userId", u."userName", r."roleCode", u."departmentId", u."isActive" '
                'FROM "ErpAuthExpenseUsers" u JOIN "ErpMasterExpenseRole" r ON u."roleId" = r."roleId" '
                'ORDER BY u."userName"'
            )
        ).fetchall()
        print("seeded_users:")
        for row in rows:
            print(" ", row)
    else:
        print("ErpAuthExpenseUsers: MISSING")

    if "ErpExpenseHodAssignment" in tables:
        rows = c.execute(text('SELECT "hodAssignmentId", "userId", "departmentId" FROM "ErpExpenseHodAssignment"')).fetchall()
        print("hod_assignments:", rows)

    if "ErpExpenseCategory" in tables:
        rows = c.execute(text('SELECT "categoryId", "categoryName", "owningDepartmentId" FROM "ErpExpenseCategory"')).fetchall()
        print("categories:", rows)

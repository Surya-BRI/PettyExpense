"""One-off script: assign Sales department to any employee accounts that have no department.

This fixes accounts (e.g. dev_uae, dev_ksa, dev_oman) that exist in ErpAuthExpenseUsers
with department_id = NULL, causing their submitted bills to be stuck in the HOD queue
visible to nobody.

Safe to re-run — only updates rows that still have no department.

Usage:
    cd backend
    python -m scripts.assign_missing_dept_to_sales
"""

from database.models import ErpAuthExpenseUsers, ErpExpenseDepartment, SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        sales = db.query(ErpExpenseDepartment).filter(
            ErpExpenseDepartment.department_name == "Sales"
        ).first()
        if not sales:
            print("ERROR: Sales department not found in ErpExpenseDepartment.")
            return

        # Only fix employee-role accounts with no department.
        # Accountant / finance_manager / admin legitimately have no department.
        no_dept = (
            db.query(ErpAuthExpenseUsers)
            .join(ErpAuthExpenseUsers.role)
            .filter(
                ErpAuthExpenseUsers.department_id.is_(None),
                ErpAuthExpenseUsers.role.has(role_code="employee"),
                ErpAuthExpenseUsers.is_active == 1,
            )
            .all()
        )

        if not no_dept:
            print("No employee accounts without a department found.")
            return

        for u in no_dept:
            print(f"  Assigning Sales to: {u.user_name} (id={u.user_id})")
            u.department_id = sales.department_id

        db.commit()
        print(f"\nDone — {len(no_dept)} account(s) assigned to Sales.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from database.models import (
    ErpExpenseApproverDelegation,
    ErpExpenseCategory,
    ErpExpenseDepartment,
    ErpExpenseHodAssignment,
    ErpExpenseRegionConfig,
    ErpExpenseVendor,
)


def department_to_dict(d: ErpExpenseDepartment) -> dict[str, Any]:
    return {"id": d.department_id, "name": d.department_name, "is_active": bool(d.is_active)}


def region_to_dict(r: ErpExpenseRegionConfig) -> dict[str, Any]:
    return {
        "id": r.region_id,
        "region_code": r.region_code,
        "region_name": r.region_name,
        "allocation_model": r.allocation_model,
        "approval_matrix": json.loads(r.approval_matrix_json) if r.approval_matrix_json else None,
        "petty_cash_hard_limit_enabled": bool(r.petty_cash_hard_limit_enabled),
        "company_name": r.company_name,
        "logo_url": r.logo_url,
        "brand_color": r.brand_color,
        "is_active": bool(r.is_active),
    }


def category_to_dict(c: ErpExpenseCategory) -> dict[str, Any]:
    return {
        "id": c.category_id,
        "name": c.category_name,
        "name_ar": c.category_name_ar,
        "owning_department_id": c.owning_department_id,
        "is_active": bool(c.is_active),
    }


def vendor_to_dict(v: ErpExpenseVendor) -> dict[str, Any]:
    return {
        "id": v.vendor_id,
        "name": v.vendor_name,
        "trn_number": v.trn_number,
        "source": v.source,
        "is_active": bool(v.is_active),
    }


def hod_assignment_to_dict(a: ErpExpenseHodAssignment) -> dict[str, Any]:
    return {
        "id": a.hod_assignment_id,
        "user_id": a.user_id,
        "department_id": a.department_id,
        "is_active": bool(a.is_active),
    }


def delegation_to_dict(d: ErpExpenseApproverDelegation) -> dict[str, Any]:
    return {
        "id": d.delegation_id,
        "approver_id": d.approver_id,
        "backup_id": d.backup_id,
        "start_date": d.start_date,
        "end_date": d.end_date,
    }


class ConfigService:
    # -- Departments --
    def list_departments(self, db: Session) -> list[dict[str, Any]]:
        return [department_to_dict(d) for d in db.query(ErpExpenseDepartment).all()]

    def create_department(self, db: Session, name: str) -> dict[str, Any]:
        d = ErpExpenseDepartment(department_name=name, is_active=1)
        db.add(d)
        db.commit()
        db.refresh(d)
        return department_to_dict(d)

    # -- Regions --
    def list_regions(self, db: Session) -> list[dict[str, Any]]:
        return [region_to_dict(r) for r in db.query(ErpExpenseRegionConfig).all()]

    def create_region(self, db: Session, body: dict[str, Any]) -> dict[str, Any]:
        r = ErpExpenseRegionConfig(
            region_code=body["region_code"],
            region_name=body["region_name"],
            allocation_model=body.get("allocation_model", "petty_cash"),
            approval_matrix_json=json.dumps(body["approval_matrix"]),
            petty_cash_hard_limit_enabled=int(bool(body.get("petty_cash_hard_limit_enabled", False))),
            company_name=body.get("company_name"),
            logo_url=body.get("logo_url"),
            brand_color=body.get("brand_color"),
            is_active=1,
        )
        db.add(r)
        db.commit()
        db.refresh(r)
        return region_to_dict(r)

    def update_region(self, db: Session, region_id: int, body: dict[str, Any]) -> dict[str, Any]:
        r = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_id == region_id).first()
        if not r:
            raise LookupError("Region not found")
        if "region_name" in body and body["region_name"] is not None:
            r.region_name = body["region_name"]
        if "allocation_model" in body and body["allocation_model"] is not None:
            r.allocation_model = body["allocation_model"]
        if "approval_matrix" in body and body["approval_matrix"] is not None:
            r.approval_matrix_json = json.dumps(body["approval_matrix"])
        if "petty_cash_hard_limit_enabled" in body and body["petty_cash_hard_limit_enabled"] is not None:
            r.petty_cash_hard_limit_enabled = int(bool(body["petty_cash_hard_limit_enabled"]))
        if "company_name" in body:
            r.company_name = body["company_name"]
        if "logo_url" in body:
            r.logo_url = body["logo_url"]
        if "brand_color" in body:
            r.brand_color = body["brand_color"]
        db.commit()
        db.refresh(r)
        return region_to_dict(r)

    # -- Categories --
    def list_categories(self, db: Session) -> list[dict[str, Any]]:
        return [category_to_dict(c) for c in db.query(ErpExpenseCategory).all()]

    def create_category(self, db: Session, body: dict[str, Any]) -> dict[str, Any]:
        if body.get("owning_department_id") is not None:
            if not db.query(ErpExpenseDepartment).filter(
                ErpExpenseDepartment.department_id == body["owning_department_id"]
            ).first():
                raise ValueError("owning_department_id does not exist")
        c = ErpExpenseCategory(
            category_name=body["name"],
            category_name_ar=body.get("name_ar"),
            owning_department_id=body.get("owning_department_id"),
            is_active=1,
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        return category_to_dict(c)

    def update_category(self, db: Session, category_id: int, body: dict[str, Any]) -> dict[str, Any]:
        c = db.query(ErpExpenseCategory).filter(ErpExpenseCategory.category_id == category_id).first()
        if not c:
            raise LookupError("Category not found")
        if "name" in body and body["name"] is not None:
            c.category_name = body["name"]
        if "name_ar" in body:
            c.category_name_ar = body["name_ar"]
        if "owning_department_id" in body:
            c.owning_department_id = body["owning_department_id"]
        if "is_active" in body and body["is_active"] is not None:
            c.is_active = int(bool(body["is_active"]))
        db.commit()
        db.refresh(c)
        return category_to_dict(c)

    def delete_category(self, db: Session, category_id: int) -> None:
        c = db.query(ErpExpenseCategory).filter(ErpExpenseCategory.category_id == category_id).first()
        if not c:
            raise LookupError("Category not found")
        db.delete(c)
        db.commit()

    # -- Vendors --
    def list_vendors(self, db: Session) -> list[dict[str, Any]]:
        return [vendor_to_dict(v) for v in db.query(ErpExpenseVendor).all()]

    def create_vendor(self, db: Session, body: dict[str, Any]) -> dict[str, Any]:
        v = ErpExpenseVendor(
            vendor_name=body["name"],
            trn_number=body.get("trn_number"),
            source=body.get("source", "manual"),
            is_active=1,
        )
        db.add(v)
        db.commit()
        db.refresh(v)
        return vendor_to_dict(v)

    def delete_vendor(self, db: Session, vendor_id: int) -> None:
        v = db.query(ErpExpenseVendor).filter(ErpExpenseVendor.vendor_id == vendor_id).first()
        if not v:
            raise LookupError("Vendor not found")
        db.delete(v)
        db.commit()

    # -- HOD assignments (Phase 2) --
    def list_hod_assignments(self, db: Session) -> list[dict[str, Any]]:
        return [hod_assignment_to_dict(a) for a in db.query(ErpExpenseHodAssignment).all()]

    def create_hod_assignment(self, db: Session, user_id: int, department_id: int) -> dict[str, Any]:
        a = ErpExpenseHodAssignment(user_id=user_id, department_id=department_id, is_active=1)
        db.add(a)
        db.commit()
        db.refresh(a)
        return hod_assignment_to_dict(a)

    # -- Approver delegations (Phase 2) --
    def list_delegations(self, db: Session) -> list[dict[str, Any]]:
        return [delegation_to_dict(d) for d in db.query(ErpExpenseApproverDelegation).all()]

    def create_delegation(self, db: Session, approver_id: int, backup_id: int, start_date: str, end_date: str) -> dict[str, Any]:
        d = ErpExpenseApproverDelegation(
            approver_id=approver_id, backup_id=backup_id, start_date=start_date, end_date=end_date
        )
        db.add(d)
        db.commit()
        db.refresh(d)
        return delegation_to_dict(d)


config_service = ConfigService()

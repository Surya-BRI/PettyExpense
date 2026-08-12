import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session, joinedload

from auth.security import CurrentUser
from database.models import (
    ErpAuthExpenseUsers,
    ErpExpenseApprovalHistory,
    ErpExpenseCategory,
    ErpExpenseDocument,
    ErpExpenseRegionConfig,
    ErpExpenseTransaction,
    ErpExpenseVendor,
)
from services.email_service import email_service
from services.ocr_service import ocr_service
from services.storage import storage_service


def _history(db: Session, transaction_id: int, actor_id: int, stage: str, action: str, comment: Optional[str] = None) -> None:
    db.add(
        ErpExpenseApprovalHistory(
            transaction_id=transaction_id,
            stage=stage,
            actor_id=actor_id,
            action=action,
            comment=comment,
        )
    )


def _resolve_vendor(db: Session, vendor_name: Optional[str], source: str = "manual") -> Optional[ErpExpenseVendor]:
    if not vendor_name or not vendor_name.strip():
        return None
    vendor_name = vendor_name.strip()
    vendor = db.query(ErpExpenseVendor).filter(ErpExpenseVendor.vendor_name == vendor_name).first()
    if vendor:
        return vendor
    vendor = ErpExpenseVendor(vendor_name=vendor_name, source=source, is_active=1)
    db.add(vendor)
    db.flush()
    return vendor


def _resolve_region(db: Session, region_code: str) -> ErpExpenseRegionConfig:
    region = db.query(ErpExpenseRegionConfig).filter(ErpExpenseRegionConfig.region_code == region_code).first()
    if not region:
        raise ValueError(f"Unknown region_code: {region_code}")
    return region


def transaction_to_dict(txn: ErpExpenseTransaction, include_history: bool = False) -> dict[str, Any]:
    document = txn.documents[0] if txn.documents else None
    data: dict[str, Any] = {
        "id": txn.transaction_id,
        "type": txn.type,
        "employee_id": txn.employee_id,
        "region_id": txn.region_id,
        "region_code": txn.region.region_code if txn.region else None,
        "project_id": txn.project_cache_id,
        "category_id": txn.category_id,
        "category_name": txn.category.category_name if txn.category else None,
        "vendor_id": txn.vendor_id,
        "vendor_name": txn.vendor.vendor_name if txn.vendor else None,
        "bill_date": txn.bill_date,
        "currency": txn.currency,
        "exchange_rate": txn.exchange_rate,
        "amount": txn.amount,
        "vat_amount": txn.vat_amount,
        "total_amount": txn.total_amount,
        "op_number": txn.op_number,
        "status": txn.status,
        "current_stage": txn.current_stage,
        "dispute_returned": bool(txn.dispute_returned),
        "remarks": txn.remarks,
        "duplicate_flag": bool(txn.duplicate_flag),
        "created_at": txn.created_on.isoformat() if txn.created_on else None,
        "updated_at": txn.modified_on.isoformat() if txn.modified_on else None,
        "submitted_at": txn.submitted_on.isoformat() if txn.submitted_on else None,
        "decided_at": txn.decided_on.isoformat() if txn.decided_on else None,
        "paid_at": txn.paid_on.isoformat() if txn.paid_on else None,
        "receipt": None,
        "duplicate_warning": None,
    }
    if document:
        proxy = f"/api/claims/receipts/{document.document_id}/image"
        signed = storage_service.presigned_url(document.s3_key)
        data["receipt"] = {
            "id": document.document_id,
            "s3_key": document.s3_key,
            "content_type": document.content_type,
            "ocr_vendor": document.ocr_vendor,
            "ocr_amount": document.ocr_amount,
            "ocr_date": document.ocr_date,
            "ocr_confidence": document.ocr_confidence,
            "image_hash": document.hash,
            "image_url": signed or proxy,
            "image_proxy_url": proxy,
        }
    if include_history:
        data["history"] = [
            {
                "id": h.approval_history_id,
                "stage": h.stage,
                "actor_id": h.actor_id,
                "action": h.action,
                "remarks": h.comment,
                "created_at": h.acted_on.isoformat() if h.acted_on else None,
            }
            for h in sorted(txn.approval_history, key=lambda x: x.acted_on or datetime.min)
        ]
    return data


class TransactionService:
    def run_ocr(self, db: Session, image_bytes: bytes, content_type: str, filename: str) -> dict[str, Any]:
        key = storage_service.save_bytes(
            image_bytes,
            content_type=content_type,
            ext=(filename.rsplit(".", 1)[-1] if "." in filename else "jpg"),
        )
        img_hash = storage_service.image_hash(image_bytes)
        ocr = ocr_service.run(image_bytes, filename)

        document = ErpExpenseDocument(
            transaction_id=None,
            s3_key=key,
            content_type=content_type,
            ocr_raw_json=ocr.get("raw_json") if isinstance(ocr.get("raw_json"), str) else json.dumps(ocr.get("raw_json")),
            ocr_vendor=ocr.get("vendor"),
            ocr_amount=ocr.get("amount"),
            ocr_date=ocr.get("date"),
            ocr_confidence=ocr.get("confidence"),
            hash=img_hash,
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        duplicate = self._find_duplicate(db, img_hash, ocr.get("vendor"), ocr.get("amount"), ocr.get("date"))

        proxy = f"/api/claims/receipts/{document.document_id}/image"
        signed = storage_service.presigned_url(key)
        return {
            "receipt_id": document.document_id,
            "s3_key": key,
            "vendor": ocr.get("vendor"),
            "amount": ocr.get("amount"),
            "date": ocr.get("date"),
            "confidence": ocr.get("confidence"),
            "raw_text": ocr.get("raw_text"),
            "image_hash": img_hash,
            "image_url": signed or proxy,
            "image_proxy_url": proxy,
            "duplicate_warning": duplicate,
        }

    def _find_duplicate(
        self,
        db: Session,
        image_hash: Optional[str],
        vendor_name: Optional[str],
        amount: Optional[float],
        bill_date: Optional[str],
        exclude_transaction_id: Optional[int] = None,
    ) -> Optional[dict[str, Any]]:
        if image_hash:
            q = db.query(ErpExpenseDocument).filter(ErpExpenseDocument.hash == image_hash)
            if exclude_transaction_id:
                q = q.filter(ErpExpenseDocument.transaction_id != exclude_transaction_id)
            hit = q.first()
            if hit and hit.transaction_id:
                return {
                    "reason": "same_image_hash",
                    "existing_claim_id": hit.transaction_id,
                    "message": "A receipt with the same image was already uploaded.",
                }

        if vendor_name and amount is not None and bill_date:
            vendor = db.query(ErpExpenseVendor).filter(ErpExpenseVendor.vendor_name == vendor_name).first()
            if vendor:
                q = db.query(ErpExpenseTransaction).filter(
                    ErpExpenseTransaction.vendor_id == vendor.vendor_id,
                    ErpExpenseTransaction.amount == amount,
                    ErpExpenseTransaction.bill_date == bill_date,
                    ErpExpenseTransaction.status != "rejected",
                )
                if exclude_transaction_id:
                    q = q.filter(ErpExpenseTransaction.transaction_id != exclude_transaction_id)
                hit_txn = q.first()
                if hit_txn:
                    return {
                        "reason": "same_vendor_amount_date",
                        "existing_claim_id": hit_txn.transaction_id,
                        "message": "A claim with the same vendor, amount, and date already exists.",
                    }
        return None

    def create_claim(
        self,
        db: Session,
        user: CurrentUser,
        *,
        vendor: str,
        amount: float,
        vat_amount: float = 0.0,
        total_amount: Optional[float] = None,
        currency: str = "INR",
        exchange_rate: float = 1.0,
        bill_date: Optional[str],
        category_id: int,
        region_code: str,
        type: str = "reimbursement",
        project_id: Optional[int],
        op_number: Optional[str],
        remarks: Optional[str],
        receipt_id: Optional[int],
        s3_key: Optional[str],
        submit: bool = True,
    ) -> dict[str, Any]:
        region = _resolve_region(db, region_code)
        category = db.query(ErpExpenseCategory).filter(ErpExpenseCategory.category_id == category_id).first()
        if not category:
            raise ValueError("Unknown category_id")
        vendor_obj = _resolve_vendor(db, vendor, source="ocr_auto" if receipt_id or s3_key else "manual")

        txn = ErpExpenseTransaction(
            type=type,
            employee_id=user.id,
            region_id=region.region_id,
            project_cache_id=project_id,
            category_id=category.category_id,
            vendor_id=vendor_obj.vendor_id if vendor_obj else None,
            bill_date=bill_date,
            currency=currency,
            exchange_rate=exchange_rate,
            amount=amount,
            vat_amount=vat_amount,
            total_amount=total_amount if total_amount is not None else amount + vat_amount,
            op_number=op_number,
            remarks=remarks,
            status="submitted" if submit else "draft",
            submitted_on=datetime.utcnow() if submit else None,
        )
        db.add(txn)
        db.flush()

        document = None
        if receipt_id:
            document = db.query(ErpExpenseDocument).filter(ErpExpenseDocument.document_id == receipt_id).first()
        elif s3_key:
            document = db.query(ErpExpenseDocument).filter(ErpExpenseDocument.s3_key == s3_key).first()
        if document:
            document.transaction_id = txn.transaction_id

        _history(db, txn.transaction_id, user.id, "employee", "created" if not submit else "submitted")

        duplicate = self._find_duplicate(
            db, document.hash if document else None, vendor, amount, bill_date, txn.transaction_id
        )

        db.commit()
        txn = (
            db.query(ErpExpenseTransaction)
            .options(
                joinedload(ErpExpenseTransaction.documents),
                joinedload(ErpExpenseTransaction.approval_history),
                joinedload(ErpExpenseTransaction.region),
                joinedload(ErpExpenseTransaction.category),
                joinedload(ErpExpenseTransaction.vendor),
            )
            .filter(ErpExpenseTransaction.transaction_id == txn.transaction_id)
            .one()
        )
        result = transaction_to_dict(txn, include_history=True)
        result["duplicate_warning"] = duplicate

        if submit:
            self._notify_finance_on_submit(db, txn)
        return result

    def update_draft(self, db: Session, user: CurrentUser, transaction_id: int, updates: dict[str, Any]) -> dict[str, Any]:
        txn = self._owned_transaction(db, user, transaction_id)
        if txn.status != "draft":
            raise ValueError("Only draft claims can be edited")

        if "vendor" in updates and updates["vendor"]:
            vendor_obj = _resolve_vendor(db, updates["vendor"])
            txn.vendor_id = vendor_obj.vendor_id if vendor_obj else None
        for field, attr in (
            ("amount", "amount"),
            ("vat_amount", "vat_amount"),
            ("total_amount", "total_amount"),
            ("bill_date", "bill_date"),
            ("category_id", "category_id"),
            ("project_id", "project_cache_id"),
            ("op_number", "op_number"),
            ("remarks", "remarks"),
        ):
            if field in updates and updates[field] is not None:
                setattr(txn, attr, updates[field])
        _history(db, txn.transaction_id, user.id, "employee", "edited")
        db.commit()
        return self.get_claim(db, user, transaction_id)

    def submit_claim(self, db: Session, user: CurrentUser, transaction_id: int) -> dict[str, Any]:
        txn = self._owned_transaction(db, user, transaction_id)
        if txn.status not in ("draft",):
            raise ValueError("Only draft claims can be submitted")
        txn.status = "submitted"
        txn.submitted_on = datetime.utcnow()
        _history(db, txn.transaction_id, user.id, "employee", "submitted")
        db.commit()
        self._notify_finance_on_submit(db, txn)
        return self.get_claim(db, user, transaction_id)

    def list_mine(self, db: Session, user: CurrentUser) -> list[dict[str, Any]]:
        txns = (
            db.query(ErpExpenseTransaction)
            .options(
                joinedload(ErpExpenseTransaction.documents),
                joinedload(ErpExpenseTransaction.region),
                joinedload(ErpExpenseTransaction.category),
                joinedload(ErpExpenseTransaction.vendor),
            )
            .filter(ErpExpenseTransaction.employee_id == user.id)
            .order_by(ErpExpenseTransaction.created_on.desc())
            .all()
        )
        return [transaction_to_dict(t) for t in txns]

    def get_claim(self, db: Session, user: CurrentUser, transaction_id: int) -> dict[str, Any]:
        txn = (
            db.query(ErpExpenseTransaction)
            .options(
                joinedload(ErpExpenseTransaction.documents),
                joinedload(ErpExpenseTransaction.approval_history),
                joinedload(ErpExpenseTransaction.region),
                joinedload(ErpExpenseTransaction.category),
                joinedload(ErpExpenseTransaction.vendor),
            )
            .filter(ErpExpenseTransaction.transaction_id == transaction_id)
            .first()
        )
        if not txn:
            raise LookupError("Claim not found")
        if txn.employee_id != user.id and not user.is_approver:
            raise PermissionError("Not allowed")
        data = transaction_to_dict(txn, include_history=True)
        if txn.documents:
            doc = txn.documents[0]
            data["duplicate_warning"] = self._find_duplicate(
                db, doc.hash, txn.vendor.vendor_name if txn.vendor else None, txn.amount, txn.bill_date, txn.transaction_id
            )
        return data

    def list_admin(
        self,
        db: Session,
        *,
        status: Optional[str] = None,
        category_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        q = db.query(ErpExpenseTransaction).options(
            joinedload(ErpExpenseTransaction.documents),
            joinedload(ErpExpenseTransaction.region),
            joinedload(ErpExpenseTransaction.category),
            joinedload(ErpExpenseTransaction.vendor),
        )
        if status:
            q = q.filter(ErpExpenseTransaction.status == status)
        if category_id:
            q = q.filter(ErpExpenseTransaction.category_id == category_id)
        if employee_id:
            q = q.filter(ErpExpenseTransaction.employee_id == employee_id)
        if project_id:
            q = q.filter(ErpExpenseTransaction.project_cache_id == project_id)
        txns = q.order_by(ErpExpenseTransaction.created_on.desc()).all()
        return [transaction_to_dict(t) for t in txns]

    def mark_paid(self, db: Session, user: CurrentUser, transaction_id: int, remarks: Optional[str]) -> dict[str, Any]:
        txn = self._get(db, transaction_id)
        if txn.status != "approved":
            raise ValueError("Only approved claims can be marked paid")
        txn.status = "paid"
        txn.paid_on = datetime.utcnow()
        if remarks:
            txn.remarks = remarks
        _history(db, txn.transaction_id, user.id, "finance_manager", "paid", remarks)
        db.commit()
        self._notify_employee(db, txn, "paid", remarks)
        return self.get_claim(db, user, transaction_id)

    def get_receipt(self, db: Session, receipt_id: int) -> ErpExpenseDocument:
        document = db.query(ErpExpenseDocument).filter(ErpExpenseDocument.document_id == receipt_id).first()
        if not document:
            raise LookupError("Receipt not found")
        return document

    def _get(self, db: Session, transaction_id: int) -> ErpExpenseTransaction:
        txn = db.query(ErpExpenseTransaction).filter(ErpExpenseTransaction.transaction_id == transaction_id).first()
        if not txn:
            raise LookupError("Claim not found")
        return txn

    def _owned_transaction(self, db: Session, user: CurrentUser, transaction_id: int) -> ErpExpenseTransaction:
        txn = self._get(db, transaction_id)
        if txn.employee_id != user.id and not user.is_approver:
            raise PermissionError("Not allowed")
        return txn

    def _notify_finance_on_submit(self, db: Session, txn: ErpExpenseTransaction) -> None:
        approvers = (
            db.query(ErpAuthExpenseUsers)
            .join(ErpAuthExpenseUsers.role)
            .filter(ErpAuthExpenseUsers.is_active == 1)
            .all()
        )
        vendor_name = txn.vendor.vendor_name if txn.vendor else "unknown vendor"
        for u in approvers:
            if u.role.role_code == "employee":
                continue
            email_service.notify(
                u.email,
                f"New expense claim submitted ({vendor_name})",
                f"Claim {txn.transaction_id} for {txn.currency} {txn.amount} by employee #{txn.employee_id} is awaiting review.",
            )

    def _notify_employee(self, db: Session, txn: ErpExpenseTransaction, action: str, remarks: Optional[str]) -> None:
        employee = db.query(ErpAuthExpenseUsers).filter(ErpAuthExpenseUsers.user_id == txn.employee_id).first()
        email = employee.email if employee else None
        vendor_name = txn.vendor.vendor_name if txn.vendor else "unknown vendor"
        email_service.notify(
            email,
            f"Expense claim {action}: {vendor_name}",
            f"Your claim {txn.transaction_id} was {action}. Remarks: {remarks or '-'}",
        )


transaction_service = TransactionService()

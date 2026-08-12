from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from config import get_settings


class Base(DeclarativeBase):
    pass


class AuditColumns:
    """Standard ERP-Dev audit columns, present on every ErpExpense*/ErpAuthExpense*/ErpMasterExpense* table."""

    is_active: Mapped[int] = mapped_column("isActive", Integer, default=1)
    created_on: Mapped[datetime] = mapped_column("createdOn", DateTime, default=datetime.utcnow)
    created_on_zone: Mapped[Optional[datetime]] = mapped_column("createdOnZone", DateTime, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column("createdBy", Integer, nullable=True)
    modified_on: Mapped[datetime] = mapped_column(
        "modifiedOn", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    modified_on_zone: Mapped[Optional[datetime]] = mapped_column("modifiedOnZone", DateTime, nullable=True)
    modified_by: Mapped[Optional[int]] = mapped_column("modifiedBy", Integer, nullable=True)


class ErpMasterExpenseRole(Base, AuditColumns):
    """Role lookup — employee | hod | accountant | finance_manager | admin.
    department_hod is a stage name (see ErpExpenseHodAssignment), not a role row here."""

    __tablename__ = "ErpMasterExpenseRole"

    role_id: Mapped[int] = mapped_column("roleId", Integer, primary_key=True, autoincrement=True)
    role_code: Mapped[str] = mapped_column("roleCode", String(32), unique=True)
    role_name: Mapped[str] = mapped_column("roleName", String(128))


class ErpExpenseDepartment(Base, AuditColumns):
    __tablename__ = "ErpExpenseDepartment"

    department_id: Mapped[int] = mapped_column("departmentId", Integer, primary_key=True, autoincrement=True)
    department_name: Mapped[str] = mapped_column("departmentName", String(256))


class ErpAuthExpenseUsers(Base, AuditColumns):
    """App users for this module. Replaces expense_app_users — until real ErpAuthUsers is wired."""

    __tablename__ = "ErpAuthExpenseUsers"

    user_id: Mapped[int] = mapped_column("userId", Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column("userName", String(128), unique=True, index=True)
    display_name: Mapped[str] = mapped_column("displayName", String(256))
    password_hash: Mapped[str] = mapped_column("passwordHash", String(256))
    role_id: Mapped[int] = mapped_column("roleId", Integer, ForeignKey("ErpMasterExpenseRole.roleId"))
    department_id: Mapped[Optional[int]] = mapped_column(
        "departmentId", Integer, ForeignKey("ErpExpenseDepartment.departmentId"), nullable=True
    )
    email: Mapped[Optional[str]] = mapped_column("email", String(256), nullable=True)
    is_deleted: Mapped[int] = mapped_column("isDeleted", Integer, default=0)

    role: Mapped[ErpMasterExpenseRole] = relationship()
    department: Mapped[Optional[ErpExpenseDepartment]] = relationship()


class ErpExpenseRegionConfig(Base, AuditColumns):
    __tablename__ = "ErpExpenseRegionConfig"

    region_id: Mapped[int] = mapped_column("regionId", Integer, primary_key=True, autoincrement=True)
    region_code: Mapped[str] = mapped_column("regionCode", String(16), unique=True, index=True)
    region_name: Mapped[str] = mapped_column("regionName", String(256))
    allocation_model: Mapped[str] = mapped_column("allocationModel", String(32), default="petty_cash")
    approval_matrix_json: Mapped[str] = mapped_column("approvalMatrixJson", Text)
    petty_cash_hard_limit_enabled: Mapped[int] = mapped_column("pettyCashHardLimitEnabled", Integer, default=0)
    company_name: Mapped[Optional[str]] = mapped_column("companyName", String(256), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column("logoUrl", String(512), nullable=True)
    brand_color: Mapped[Optional[str]] = mapped_column("brandColor", String(16), nullable=True)


class ErpExpenseCategory(Base, AuditColumns):
    __tablename__ = "ErpExpenseCategory"

    category_id: Mapped[int] = mapped_column("categoryId", Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column("categoryName", String(128))
    category_name_ar: Mapped[Optional[str]] = mapped_column("categoryNameAr", String(128), nullable=True)
    owning_department_id: Mapped[Optional[int]] = mapped_column(
        "owningDepartmentId", Integer, ForeignKey("ErpExpenseDepartment.departmentId"), nullable=True
    )

    owning_department: Mapped[Optional[ErpExpenseDepartment]] = relationship()


class ErpExpenseVendor(Base, AuditColumns):
    __tablename__ = "ErpExpenseVendor"

    vendor_id: Mapped[int] = mapped_column("vendorId", Integer, primary_key=True, autoincrement=True)
    vendor_name: Mapped[str] = mapped_column("vendorName", String(256), index=True)
    trn_number: Mapped[Optional[str]] = mapped_column("trnNumber", String(64), nullable=True)
    source: Mapped[str] = mapped_column("source", String(32), default="manual")  # manual | ocr_auto


class ErpExpenseMultiRegionUserRegion(Base):
    __tablename__ = "ErpExpenseMultiRegionUserRegion"

    map_id: Mapped[int] = mapped_column("mapId", Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column("userId", Integer, ForeignKey("ErpAuthExpenseUsers.userId"), index=True)
    region_id: Mapped[int] = mapped_column("regionId", Integer, ForeignKey("ErpExpenseRegionConfig.regionId"))
    assigned_by: Mapped[Optional[int]] = mapped_column("assignedBy", Integer, nullable=True)
    assigned_on: Mapped[datetime] = mapped_column("assignedOn", DateTime, default=datetime.utcnow)
    is_active: Mapped[int] = mapped_column("isActive", Integer, default=1)


class ErpExpenseEmployeeCache(Base):
    """Placeholder mirror of future middleware employee sync — admin-seeded for now, not live-synced."""

    __tablename__ = "ErpExpenseEmployeeCache"

    employee_cache_id: Mapped[int] = mapped_column("employeeCacheId", Integer, primary_key=True, autoincrement=True)
    middleware_employee_id: Mapped[Optional[str]] = mapped_column("middlewareEmployeeId", String(128), nullable=True)
    employee_name: Mapped[str] = mapped_column("employeeName", String(256))
    department_id: Mapped[Optional[int]] = mapped_column(
        "departmentId", Integer, ForeignKey("ErpExpenseDepartment.departmentId"), nullable=True
    )
    region_id: Mapped[Optional[int]] = mapped_column(
        "regionId", Integer, ForeignKey("ErpExpenseRegionConfig.regionId"), nullable=True
    )
    synced_on: Mapped[Optional[datetime]] = mapped_column("syncedOn", DateTime, nullable=True)


class ErpExpenseProjectCache(Base):
    """Placeholder mirror of future middleware project/OP sync — admin-seeded for now, not live-synced."""

    __tablename__ = "ErpExpenseProjectCache"

    project_cache_id: Mapped[int] = mapped_column("projectCacheId", Integer, primary_key=True, autoincrement=True)
    middleware_project_id: Mapped[Optional[str]] = mapped_column("middlewareProjectId", String(128), nullable=True)
    project_name: Mapped[str] = mapped_column("projectName", String(256))
    op_number: Mapped[Optional[str]] = mapped_column("opNumber", String(128), nullable=True)
    region_id: Mapped[Optional[int]] = mapped_column(
        "regionId", Integer, ForeignKey("ErpExpenseRegionConfig.regionId"), nullable=True
    )
    synced_on: Mapped[Optional[datetime]] = mapped_column("syncedOn", DateTime, nullable=True)


class ErpExpenseTransaction(Base):
    __tablename__ = "ErpExpenseTransaction"

    transaction_id: Mapped[int] = mapped_column("transactionId", Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column("type", String(32), default="reimbursement")  # petty_cash | reimbursement
    employee_id: Mapped[int] = mapped_column("employeeId", Integer, ForeignKey("ErpAuthExpenseUsers.userId"), index=True)
    region_id: Mapped[int] = mapped_column("regionId", Integer, ForeignKey("ErpExpenseRegionConfig.regionId"), index=True)
    project_cache_id: Mapped[Optional[int]] = mapped_column(
        "projectCacheId", Integer, ForeignKey("ErpExpenseProjectCache.projectCacheId"), nullable=True
    )
    category_id: Mapped[int] = mapped_column("categoryId", Integer, ForeignKey("ErpExpenseCategory.categoryId"))
    vendor_id: Mapped[Optional[int]] = mapped_column(
        "vendorId", Integer, ForeignKey("ErpExpenseVendor.vendorId"), nullable=True
    )
    bill_date: Mapped[Optional[str]] = mapped_column("billDate", String(32), nullable=True)
    currency: Mapped[str] = mapped_column("currency", String(8), default="INR")
    exchange_rate: Mapped[float] = mapped_column("exchangeRate", Float, default=1.0)
    amount: Mapped[float] = mapped_column("amount", Float, default=0.0)
    vat_amount: Mapped[float] = mapped_column("vatAmount", Float, default=0.0)
    total_amount: Mapped[float] = mapped_column("totalAmount", Float, default=0.0)
    status: Mapped[str] = mapped_column("status", String(32), default="draft", index=True)
    # Phase 2 workflow-engine columns (added in the Phase 1 migration to avoid a second ALTER):
    current_stage: Mapped[Optional[str]] = mapped_column("currentStage", String(32), nullable=True)
    dispute_returned: Mapped[int] = mapped_column("disputeReturned", Integer, default=0)
    stage_due_at: Mapped[Optional[datetime]] = mapped_column("stageDueAt", DateTime, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column("remarks", Text, nullable=True)
    duplicate_flag: Mapped[int] = mapped_column("duplicateFlag", Integer, default=0)
    ocr_confidence_json: Mapped[Optional[str]] = mapped_column("ocrConfidenceJson", Text, nullable=True)
    op_number: Mapped[Optional[str]] = mapped_column("opNumber", String(128), nullable=True)
    created_on: Mapped[datetime] = mapped_column("createdOn", DateTime, default=datetime.utcnow)
    modified_on: Mapped[datetime] = mapped_column(
        "modifiedOn", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    submitted_on: Mapped[Optional[datetime]] = mapped_column("submittedOn", DateTime, nullable=True)
    decided_on: Mapped[Optional[datetime]] = mapped_column("decidedOn", DateTime, nullable=True)
    paid_on: Mapped[Optional[datetime]] = mapped_column("paidOn", DateTime, nullable=True)

    documents: Mapped[list["ErpExpenseDocument"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )
    approval_history: Mapped[list["ErpExpenseApprovalHistory"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )
    employee: Mapped[ErpAuthExpenseUsers] = relationship()
    region: Mapped[ErpExpenseRegionConfig] = relationship()
    category: Mapped[ErpExpenseCategory] = relationship()
    vendor: Mapped[Optional[ErpExpenseVendor]] = relationship()
    project: Mapped[Optional[ErpExpenseProjectCache]] = relationship()


class ErpExpenseDocument(Base):
    __tablename__ = "ErpExpenseDocument"

    document_id: Mapped[int] = mapped_column("documentId", Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[Optional[int]] = mapped_column(
        "transactionId", Integer, ForeignKey("ErpExpenseTransaction.transactionId"), nullable=True, index=True
    )
    s3_key: Mapped[str] = mapped_column("s3Key", String(512))
    content_type: Mapped[str] = mapped_column("contentType", String(128), default="image/jpeg")
    ocr_raw_json: Mapped[Optional[str]] = mapped_column("ocrRawJson", Text, nullable=True)
    ocr_vendor: Mapped[Optional[str]] = mapped_column("ocrVendor", String(256), nullable=True)
    ocr_amount: Mapped[Optional[float]] = mapped_column("ocrAmount", Float, nullable=True)
    ocr_date: Mapped[Optional[str]] = mapped_column("ocrDate", String(32), nullable=True)
    ocr_confidence: Mapped[Optional[float]] = mapped_column("ocrConfidence", Float, nullable=True)
    hash: Mapped[Optional[str]] = mapped_column("hash", String(128), nullable=True, index=True)
    uploaded_on: Mapped[datetime] = mapped_column("uploadedOn", DateTime, default=datetime.utcnow)

    transaction: Mapped[Optional[ErpExpenseTransaction]] = relationship(back_populates="documents")


class ErpExpenseHodAssignment(Base):
    """Which department(s) a user is HOD of. Drives both the 'hod' stage (employee's own department)
    and the 'department_hod' stage (category's owning department) lookups, plus the same-person auto-skip."""

    __tablename__ = "ErpExpenseHodAssignment"

    hod_assignment_id: Mapped[int] = mapped_column("hodAssignmentId", Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column("userId", Integer, ForeignKey("ErpAuthExpenseUsers.userId"), index=True)
    department_id: Mapped[int] = mapped_column(
        "departmentId", Integer, ForeignKey("ErpExpenseDepartment.departmentId"), index=True
    )
    is_active: Mapped[int] = mapped_column("isActive", Integer, default=1)


class ErpExpenseApprovalHistory(Base):
    __tablename__ = "ErpExpenseApprovalHistory"

    approval_history_id: Mapped[int] = mapped_column("approvalHistoryId", Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(
        "transactionId", Integer, ForeignKey("ErpExpenseTransaction.transactionId"), index=True
    )
    stage: Mapped[str] = mapped_column("stage", String(32))  # hod | department_hod | accountant | finance_manager
    actor_id: Mapped[int] = mapped_column("actorId", Integer, ForeignKey("ErpAuthExpenseUsers.userId"))
    action: Mapped[str] = mapped_column("action", String(32))  # approve | dispute | reject
    comment: Mapped[Optional[str]] = mapped_column("comment", Text, nullable=True)
    acted_on: Mapped[datetime] = mapped_column("actedOn", DateTime, default=datetime.utcnow)

    transaction: Mapped[ErpExpenseTransaction] = relationship(back_populates="approval_history")


class ErpExpenseApproverDelegation(Base):
    __tablename__ = "ErpExpenseApproverDelegation"

    delegation_id: Mapped[int] = mapped_column("delegationId", Integer, primary_key=True, autoincrement=True)
    approver_id: Mapped[int] = mapped_column("approverId", Integer, ForeignKey("ErpAuthExpenseUsers.userId"), index=True)
    backup_id: Mapped[int] = mapped_column("backupId", Integer, ForeignKey("ErpAuthExpenseUsers.userId"))
    start_date: Mapped[str] = mapped_column("startDate", String(32))  # ISO date string
    end_date: Mapped[str] = mapped_column("endDate", String(32))
    created_on: Mapped[datetime] = mapped_column("createdOn", DateTime, default=datetime.utcnow)


settings = get_settings()
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=1800,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

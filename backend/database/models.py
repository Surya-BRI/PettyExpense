from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Unicode,
    UnicodeText,
    UniqueConstraint,
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
    display_name: Mapped[str] = mapped_column("displayName", Unicode(256))
    password_hash: Mapped[str] = mapped_column("passwordHash", String(256))
    role_id: Mapped[int] = mapped_column("roleId", Integer, ForeignKey("ErpMasterExpenseRole.roleId"))
    department_id: Mapped[Optional[int]] = mapped_column(
        "departmentId", Integer, ForeignKey("ErpExpenseDepartment.departmentId"), nullable=True
    )
    email: Mapped[Optional[str]] = mapped_column("email", String(256), nullable=True)
    is_deleted: Mapped[int] = mapped_column("isDeleted", Integer, default=0)
    # New column on an existing table — create_all() will not add it, run the ALTER script separately.
    language_preference: Mapped[str] = mapped_column("languagePreference", String(8), default="en")
    # Company the person belongs to in ERP, saved at login so approval routing never has to ask
    # ERP. Together with ErpExpenseMultiRegionUserRegion it is the set of companies whose bills
    # they handle. New column: see scripts/add_currency_region_payment_schema.py.
    home_region_id: Mapped[Optional[int]] = mapped_column("homeRegionId", Integer, nullable=True)

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
    company_name: Mapped[Optional[str]] = mapped_column("companyName", Unicode(256), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column("logoUrl", String(512), nullable=True)
    brand_color: Mapped[Optional[str]] = mapped_column("brandColor", String(16), nullable=True)
    # The company's books currency: bills are converted into it and its petty-cash funds are
    # held in it. New column: see scripts/add_currency_region_payment_schema.py.
    base_currency: Mapped[Optional[str]] = mapped_column("baseCurrency", String(8), nullable=True)


class ErpExpenseCategory(Base, AuditColumns):
    __tablename__ = "ErpExpenseCategory"

    category_id: Mapped[int] = mapped_column("categoryId", Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column("categoryName", Unicode(128))
    category_name_ar: Mapped[Optional[str]] = mapped_column("categoryNameAr", Unicode(128), nullable=True)
    owning_department_id: Mapped[Optional[int]] = mapped_column(
        "owningDepartmentId", Integer, ForeignKey("ErpExpenseDepartment.departmentId"), nullable=True
    )

    owning_department: Mapped[Optional[ErpExpenseDepartment]] = relationship()


class ErpExpenseVendor(Base, AuditColumns):
    __tablename__ = "ErpExpenseVendor"

    vendor_id: Mapped[int] = mapped_column("vendorId", Integer, primary_key=True, autoincrement=True)
    vendor_name: Mapped[str] = mapped_column("vendorName", Unicode(256), index=True)
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


class ErpExpensePettyCashFund(Base, AuditColumns):
    """App-owned department PCA pot. ERP does not store limits.

    openingBalance is the approved limit. Available = limit − unreplenished petty-cash spend.
    Approved top-ups replenish spend; they never raise the limit. BRI / DUBAI is
    department-only (ownerType=department).
    """

    __tablename__ = "ErpExpensePettyCashFund"

    fund_id: Mapped[int] = mapped_column("fundId", Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(
        "regionId", Integer, ForeignKey("ErpExpenseRegionConfig.regionId"), index=True
    )
    owner_type: Mapped[str] = mapped_column("ownerType", String(16))  # department | employee
    department_id: Mapped[Optional[int]] = mapped_column(
        "departmentId", Integer, ForeignKey("ErpExpenseDepartment.departmentId"), nullable=True, index=True
    )
    employee_id: Mapped[Optional[int]] = mapped_column(
        "employeeId", Integer, ForeignKey("ErpAuthExpenseUsers.userId"), nullable=True, index=True
    )
    currency: Mapped[str] = mapped_column("currency", String(8), default="AED")
    opening_balance: Mapped[float] = mapped_column("openingBalance", Float, default=0.0)
    # Employee-advance companies (Professional Signs): one advance per employee per project.
    # The project's OP code (ErpMasterOpportunity.salesForceCode) and its name, copied from ERP
    # when the HOD proposes the advance. Null on department pots.
    # New columns: see scripts/add_employee_pca_columns.py.
    op_number: Mapped[Optional[str]] = mapped_column("opNumber", String(128), nullable=True)
    op_name: Mapped[Optional[str]] = mapped_column("opName", Unicode(256), nullable=True)

    region: Mapped[ErpExpenseRegionConfig] = relationship()
    department: Mapped[Optional[ErpExpenseDepartment]] = relationship()
    employee: Mapped[Optional[ErpAuthExpenseUsers]] = relationship()
    topups: Mapped[list["ErpExpenseFundTopupRequest"]] = relationship(back_populates="fund")


class ErpExpenseFundTopupRequest(Base, AuditColumns):
    """PCA replenishment: HOD/Admin request → Accounts verify → Finance approve + payment."""

    __tablename__ = "ErpExpenseFundTopupRequest"

    topup_id: Mapped[int] = mapped_column("topupId", Integer, primary_key=True, autoincrement=True)
    fund_id: Mapped[int] = mapped_column(
        "fundId", Integer, ForeignKey("ErpExpensePettyCashFund.fundId"), index=True
    )
    amount: Mapped[float] = mapped_column("amount", Float)
    requester_id: Mapped[int] = mapped_column("requesterId", Integer, ForeignKey("ErpAuthExpenseUsers.userId"))
    status: Mapped[str] = mapped_column("status", String(16), default="submitted", index=True)
    remarks: Mapped[Optional[str]] = mapped_column("remarks", UnicodeText, nullable=True)
    verified_by: Mapped[Optional[int]] = mapped_column(
        "verifiedBy", Integer, ForeignKey("ErpAuthExpenseUsers.userId"), nullable=True
    )
    verified_on: Mapped[Optional[datetime]] = mapped_column("verifiedOn", DateTime, nullable=True)
    decided_by: Mapped[Optional[int]] = mapped_column(
        "decidedBy", Integer, ForeignKey("ErpAuthExpenseUsers.userId"), nullable=True
    )
    decided_on: Mapped[Optional[datetime]] = mapped_column("decidedOn", DateTime, nullable=True)
    payment_method: Mapped[Optional[str]] = mapped_column("paymentMethod", String(32), nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column("paymentReference", String(128), nullable=True)
    payment_date: Mapped[Optional[datetime]] = mapped_column("paymentDate", DateTime, nullable=True)
    # Employee-advance companies (Professional Signs), see services/employee_pca_service.py:
    # kind 'advance' = giving / raising an employee's PCA (HOD proposes -> Accounts Manager
    # approves -> Accounts Department pays); kind 'topup' = replenishing spent bills.
    # New columns: see scripts/add_employee_pca_columns.py.
    kind: Mapped[str] = mapped_column("kind", String(16), default="topup")
    hod_approved_by: Mapped[Optional[int]] = mapped_column(
        "hodApprovedBy", Integer, ForeignKey("ErpAuthExpenseUsers.userId"), nullable=True
    )
    hod_approved_on: Mapped[Optional[datetime]] = mapped_column("hodApprovedOn", DateTime, nullable=True)
    payment_source: Mapped[Optional[str]] = mapped_column("paymentSource", String(32), nullable=True)
    paid_by: Mapped[Optional[int]] = mapped_column(
        "paidBy", Integer, ForeignKey("ErpAuthExpenseUsers.userId"), nullable=True
    )

    fund: Mapped[ErpExpensePettyCashFund] = relationship(back_populates="topups")
    requester: Mapped[ErpAuthExpenseUsers] = relationship(foreign_keys=[requester_id])
    verifier: Mapped[Optional[ErpAuthExpenseUsers]] = relationship(foreign_keys=[verified_by])
    decider: Mapped[Optional[ErpAuthExpenseUsers]] = relationship(foreign_keys=[decided_by])
    hod_approver: Mapped[Optional[ErpAuthExpenseUsers]] = relationship(foreign_keys=[hod_approved_by])
    payer: Mapped[Optional[ErpAuthExpenseUsers]] = relationship(foreign_keys=[paid_by])
    bills: Mapped[list["ErpExpenseFundTopupBill"]] = relationship(back_populates="topup")
    history: Mapped[list["ErpExpenseTopupHistory"]] = relationship(
        back_populates="topup", order_by="ErpExpenseTopupHistory.history_id"
    )


class ErpExpenseFundTopupBill(Base):
    """Bills attached to a PCA top-up so Finance can reconcile the common bank account."""

    __tablename__ = "ErpExpenseFundTopupBill"

    map_id: Mapped[int] = mapped_column("mapId", Integer, primary_key=True, autoincrement=True)
    topup_id: Mapped[int] = mapped_column(
        "topupId", Integer, ForeignKey("ErpExpenseFundTopupRequest.topupId"), index=True
    )
    transaction_id: Mapped[int] = mapped_column(
        "transactionId", Integer, ForeignKey("ErpExpenseTransaction.transactionId"), index=True
    )
    amount: Mapped[float] = mapped_column("amount", Float)

    topup: Mapped[ErpExpenseFundTopupRequest] = relationship(back_populates="bills")
    transaction: Mapped["ErpExpenseTransaction"] = relationship()


class ErpExpenseTopupHistory(Base):
    """Audit log of a PCA top-up: one row per step (requested, verified, returned, approved,
    rejected) with who, when and their comment. New table -- create_all() creates it on startup."""

    __tablename__ = "ErpExpenseTopupHistory"

    history_id: Mapped[int] = mapped_column("historyId", Integer, primary_key=True, autoincrement=True)
    topup_id: Mapped[int] = mapped_column(
        "topupId", Integer, ForeignKey("ErpExpenseFundTopupRequest.topupId"), index=True
    )
    actor_id: Mapped[int] = mapped_column("actorId", Integer, ForeignKey("ErpAuthExpenseUsers.userId"))
    action: Mapped[str] = mapped_column("action", String(16))
    comment: Mapped[Optional[str]] = mapped_column("comment", UnicodeText, nullable=True)
    acted_on: Mapped[datetime] = mapped_column("actedOn", DateTime, default=datetime.utcnow)

    topup: Mapped[ErpExpenseFundTopupRequest] = relationship(back_populates="history")
    actor: Mapped[ErpAuthExpenseUsers] = relationship()


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
    currency: Mapped[str] = mapped_column("currency", String(8), default="AED")
    exchange_rate: Mapped[float] = mapped_column("exchangeRate", Float, default=1.0)
    amount: Mapped[float] = mapped_column("amount", Float, default=0.0)
    vat_amount: Mapped[float] = mapped_column("vatAmount", Float, default=0.0)
    total_amount: Mapped[float] = mapped_column("totalAmount", Float, default=0.0)
    status: Mapped[str] = mapped_column("status", String(32), default="draft", index=True)
    # Phase 2 workflow-engine columns (added in the Phase 1 migration to avoid a second ALTER):
    current_stage: Mapped[Optional[str]] = mapped_column("currentStage", String(32), nullable=True)
    dispute_returned: Mapped[int] = mapped_column("disputeReturned", Integer, default=0)
    stage_due_at: Mapped[Optional[datetime]] = mapped_column("stageDueAt", DateTime, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column("remarks", UnicodeText, nullable=True)
    duplicate_flag: Mapped[int] = mapped_column("duplicateFlag", Integer, default=0)
    # The bill's vendor as plain text (typed or OCR'd). There is no vendor matching: new bills
    # leave vendor_id null. Older rows may still carry a vendor_id from the removed matching.
    # New column on an existing table -- create_all() won't add it, see scripts/add_vendor_raw_text_column.py.
    vendor_raw_text: Mapped[Optional[str]] = mapped_column("vendorRawText", Unicode(256), nullable=True)
    ocr_confidence_json: Mapped[Optional[str]] = mapped_column("ocrConfidenceJson", Text, nullable=True)
    op_number: Mapped[Optional[str]] = mapped_column("opNumber", String(128), nullable=True)
    # Bill/invoice number as printed on the receipt — extracted by OCR, editable by the employee.
    # New column: create_all() won't add it; run scripts/add_bill_number_column.py once.
    bill_number: Mapped[Optional[str]] = mapped_column("billNumber", String(128), nullable=True)
    # Conversion into the company's base currency, locked at first submit (a dispute → resubmit
    # keeps it unless the bill currency or company changes). exchangeRateDate is the date of
    # the published rate actually used. New columns: see scripts/add_currency_region_payment_schema.py.
    base_currency: Mapped[Optional[str]] = mapped_column("baseCurrency", String(8), nullable=True)
    exchange_rate_date: Mapped[Optional[str]] = mapped_column("exchangeRateDate", String(32), nullable=True)
    exchange_rate_source: Mapped[Optional[str]] = mapped_column("exchangeRateSource", String(32), nullable=True)
    amount_base: Mapped[Optional[float]] = mapped_column("amountBase", Float, nullable=True)
    vat_amount_base: Mapped[Optional[float]] = mapped_column("vatAmountBase", Float, nullable=True)
    total_amount_base: Mapped[Optional[float]] = mapped_column("totalAmountBase", Float, nullable=True)
    # Expense journal booked by Accounts for this bill (Professional Signs: EJV, or EJVB for a
    # multi-branch transaction) and its number in ERP. Required at the stage named by the
    # company's `journal_required_at`. New columns: see scripts/add_employee_pca_columns.py.
    journal_type: Mapped[Optional[str]] = mapped_column("journalType", String(8), nullable=True)
    journal_reference: Mapped[Optional[str]] = mapped_column("journalReference", Unicode(64), nullable=True)
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
    line_items: Mapped[list["ErpExpenseLineItem"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan", order_by="ErpExpenseLineItem.line_no"
    )
    employee: Mapped[ErpAuthExpenseUsers] = relationship()
    region: Mapped[ErpExpenseRegionConfig] = relationship()
    category: Mapped[ErpExpenseCategory] = relationship()
    vendor: Mapped[Optional[ErpExpenseVendor]] = relationship()
    project: Mapped[Optional[ErpExpenseProjectCache]] = relationship()
    payment: Mapped[Optional["ErpExpensePaymentRecord"]] = relationship(
        back_populates="transaction", uselist=False
    )


class ErpExpensePaymentRecord(Base, AuditColumns):
    """Spec 5.5 payment_records: how and when Finance paid an approved reimbursement.
    One row per claim. New table -- create_all() creates it on startup."""

    __tablename__ = "ErpExpensePaymentRecord"

    payment_id: Mapped[int] = mapped_column("paymentId", Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(
        "transactionId", Integer, ForeignKey("ErpExpenseTransaction.transactionId"), unique=True, index=True
    )
    amount: Mapped[float] = mapped_column("amount", Float)
    currency: Mapped[str] = mapped_column("currency", String(8))
    payment_method: Mapped[str] = mapped_column("paymentMethod", String(32))  # bank_transfer | cash | payroll | cheque
    payment_reference: Mapped[str] = mapped_column("paymentReference", Unicode(128))
    payment_date: Mapped[datetime] = mapped_column("paymentDate", DateTime)
    paid_by: Mapped[int] = mapped_column("paidBy", Integer, ForeignKey("ErpAuthExpenseUsers.userId"))
    remarks: Mapped[Optional[str]] = mapped_column("remarks", UnicodeText, nullable=True)
    # Professional Signs (PDF section 7): 'bank' = Process 1, cash withdrawal from bank;
    # 'accounts_petty_cash' = Process 2, direct payment by the Accounts Department. Null elsewhere.
    # New column -- see scripts/add_employee_pca_columns.py.
    payment_source: Mapped[Optional[str]] = mapped_column("paymentSource", String(32), nullable=True)

    transaction: Mapped["ErpExpenseTransaction"] = relationship(back_populates="payment")
    payer: Mapped[ErpAuthExpenseUsers] = relationship(foreign_keys=[paid_by])


class ErpExpenseDocument(Base):
    __tablename__ = "ErpExpenseDocument"

    document_id: Mapped[int] = mapped_column("documentId", Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[Optional[int]] = mapped_column(
        "transactionId", Integer, ForeignKey("ErpExpenseTransaction.transactionId"), nullable=True, index=True
    )
    s3_key: Mapped[str] = mapped_column("s3Key", String(512))
    content_type: Mapped[str] = mapped_column("contentType", String(128), default="image/jpeg")
    ocr_raw_json: Mapped[Optional[str]] = mapped_column("ocrRawJson", UnicodeText, nullable=True)
    ocr_vendor: Mapped[Optional[str]] = mapped_column("ocrVendor", Unicode(256), nullable=True)
    ocr_amount: Mapped[Optional[float]] = mapped_column("ocrAmount", Float, nullable=True)
    ocr_vat_amount: Mapped[Optional[float]] = mapped_column("ocrVatAmount", Float, nullable=True)
    ocr_total_amount: Mapped[Optional[float]] = mapped_column("ocrTotalAmount", Float, nullable=True)
    ocr_currency: Mapped[Optional[str]] = mapped_column("ocrCurrency", String(8), nullable=True)
    ocr_date: Mapped[Optional[str]] = mapped_column("ocrDate", String(32), nullable=True)
    ocr_confidence: Mapped[Optional[float]] = mapped_column("ocrConfidence", Float, nullable=True)
    hash: Mapped[Optional[str]] = mapped_column("hash", String(128), nullable=True, index=True)
    uploaded_on: Mapped[datetime] = mapped_column("uploadedOn", DateTime, default=datetime.utcnow)

    transaction: Mapped[Optional[ErpExpenseTransaction]] = relationship(back_populates="documents")
    # Pages 2..N of a multi-page bill; page 1 is this row's own s3_key.
    pages: Mapped[list["ErpExpenseDocumentPage"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="ErpExpenseDocumentPage.page_no"
    )


class ErpExpenseDocumentPage(Base):
    """An extra page (2..N) of a multi-page bill. New table -- create_all() creates it on startup."""

    __tablename__ = "ErpExpenseDocumentPage"

    page_id: Mapped[int] = mapped_column("pageId", Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        "documentId", Integer, ForeignKey("ErpExpenseDocument.documentId"), nullable=False, index=True
    )
    page_no: Mapped[int] = mapped_column("pageNo", Integer)
    s3_key: Mapped[str] = mapped_column("s3Key", String(512))
    content_type: Mapped[str] = mapped_column("contentType", String(128), default="image/jpeg")
    hash: Mapped[Optional[str]] = mapped_column("hash", String(128), nullable=True)
    uploaded_on: Mapped[datetime] = mapped_column("uploadedOn", DateTime, default=datetime.utcnow)

    document: Mapped["ErpExpenseDocument"] = relationship(back_populates="pages")


class ErpExpenseLineItem(Base):
    """One item line on a "Multiple items" bill. The transaction's total is the sum of its lines."""

    __tablename__ = "ErpExpenseLineItem"

    line_item_id: Mapped[int] = mapped_column("lineItemId", Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(
        "transactionId", Integer, ForeignKey("ErpExpenseTransaction.transactionId"), index=True
    )
    line_no: Mapped[int] = mapped_column("lineNo", Integer)
    description: Mapped[str] = mapped_column("description", Unicode(512))
    quantity: Mapped[Optional[float]] = mapped_column("quantity", Float, nullable=True)
    # Line total as printed on the bill (normally VAT-inclusive).
    amount: Mapped[float] = mapped_column("amount", Float, default=0.0)
    category_id: Mapped[Optional[int]] = mapped_column(
        "categoryId", Integer, ForeignKey("ErpExpenseCategory.categoryId"), nullable=True
    )
    # Per-line project/OP override -- when null, the item belongs to the claim-level op_number.
    # New column on an existing table -- create_all() won't add it, see scripts/add_line_item_op_number_column.py.
    op_number: Mapped[Optional[str]] = mapped_column("opNumber", String(128), nullable=True)
    # VAT % as printed on the bill for this line (e.g. 5.0). Null when the bill doesn't print per-line VAT.
    # New column -- create_all() won't add it, see scripts/add_line_item_vat_percent_column.py.
    vat_percent: Mapped[Optional[float]] = mapped_column("vatPercent", Float, nullable=True)
    created_on: Mapped[datetime] = mapped_column("createdOn", DateTime, default=datetime.utcnow)

    transaction: Mapped["ErpExpenseTransaction"] = relationship(back_populates="line_items")
    category: Mapped[Optional[ErpExpenseCategory]] = relationship()


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
    comment: Mapped[Optional[str]] = mapped_column("comment", UnicodeText, nullable=True)
    acted_on: Mapped[datetime] = mapped_column("actedOn", DateTime, default=datetime.utcnow)

    transaction: Mapped[ErpExpenseTransaction] = relationship(back_populates="approval_history")
    actor: Mapped["ErpAuthExpenseUsers"] = relationship(foreign_keys=[actor_id])


class ErpExpenseApproverDelegation(Base):
    __tablename__ = "ErpExpenseApproverDelegation"

    delegation_id: Mapped[int] = mapped_column("delegationId", Integer, primary_key=True, autoincrement=True)
    approver_id: Mapped[int] = mapped_column("approverId", Integer, ForeignKey("ErpAuthExpenseUsers.userId"), index=True)
    backup_id: Mapped[int] = mapped_column("backupId", Integer, ForeignKey("ErpAuthExpenseUsers.userId"))
    start_date: Mapped[str] = mapped_column("startDate", String(32))  # ISO date string
    end_date: Mapped[str] = mapped_column("endDate", String(32))
    created_on: Mapped[datetime] = mapped_column("createdOn", DateTime, default=datetime.utcnow)


class ErpExpenseNotification(Base):
    """One row per (event, recipient, channel) delivery attempt — the audit log the spec asks for."""

    __tablename__ = "ErpExpenseNotification"
    __table_args__ = (
        UniqueConstraint("transactionId", "type", "userId", "channel", name="uqNotificationDedup"),
    )

    notification_id: Mapped[int] = mapped_column("notificationId", Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column("userId", Integer, ForeignKey("ErpAuthExpenseUsers.userId"), index=True)
    transaction_id: Mapped[Optional[int]] = mapped_column(
        "transactionId", Integer, ForeignKey("ErpExpenseTransaction.transactionId"), nullable=True, index=True
    )
    type: Mapped[str] = mapped_column("type", String(32))  # submission | dispute | rejection | approval | paid | test
    channel: Mapped[str] = mapped_column("channel", String(16))  # email | in_app
    status: Mapped[str] = mapped_column("status", String(16), default="sent")  # sent | read | failed
    message: Mapped[Optional[str]] = mapped_column("message", UnicodeText, nullable=True)
    sent_at: Mapped[datetime] = mapped_column("sentAt", DateTime, default=datetime.utcnow)


class ErpExpenseNotificationPreference(Base):
    __tablename__ = "ErpExpenseNotificationPreference"
    __table_args__ = (
        UniqueConstraint("userId", "channel", "category", name="uqNotificationPreference"),
    )

    preference_id: Mapped[int] = mapped_column("preferenceId", Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column("userId", Integer, ForeignKey("ErpAuthExpenseUsers.userId"), index=True)
    channel: Mapped[str] = mapped_column("channel", String(16))
    category: Mapped[str] = mapped_column("category", String(32))  # matches ErpExpenseNotification.type
    is_enabled: Mapped[int] = mapped_column("isEnabled", Integer, default=1)


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
    # create_all() only creates missing tables, it does not add columns to existing ones.
    # For ocrVatAmount / ocrTotalAmount / ocrCurrency on ErpExpenseDocument, run:
    #   python scripts/add_ocr_document_columns.py
    Base.metadata.create_all(bind=engine)

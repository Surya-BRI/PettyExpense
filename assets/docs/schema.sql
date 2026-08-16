-- Expense tables on ERP-Dev (SQL Server)
-- App also auto-creates these via SQLAlchemy on startup.

IF OBJECT_ID('dbo.expense_claim_history', 'U') IS NOT NULL DROP TABLE dbo.expense_claim_history;
IF OBJECT_ID('dbo.expense_receipts', 'U') IS NOT NULL DROP TABLE dbo.expense_receipts;
IF OBJECT_ID('dbo.expense_claims', 'U') IS NOT NULL DROP TABLE dbo.expense_claims;
IF OBJECT_ID('dbo.expense_app_users', 'U') IS NOT NULL DROP TABLE dbo.expense_app_users;
GO

CREATE TABLE dbo.expense_app_users (
    id NVARCHAR(64) NOT NULL PRIMARY KEY,
    username NVARCHAR(128) NOT NULL UNIQUE,
    display_name NVARCHAR(256) NOT NULL,
    password_hash NVARCHAR(256) NOT NULL,
    role NVARCHAR(32) NOT NULL DEFAULT 'salesman',
    email NVARCHAR(256) NULL,
    is_active INT NOT NULL DEFAULT 1,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE dbo.expense_claims (
    id NVARCHAR(64) NOT NULL PRIMARY KEY,
    submitted_by NVARCHAR(64) NOT NULL,
    vendor NVARCHAR(256) NOT NULL DEFAULT '',
    amount FLOAT NOT NULL DEFAULT 0,
    currency NVARCHAR(8) NOT NULL DEFAULT 'AED',
    bill_date NVARCHAR(32) NULL,
    category NVARCHAR(32) NOT NULL DEFAULT 'other',
    project_id NVARCHAR(128) NULL,
    op_number NVARCHAR(128) NULL,
    status NVARCHAR(32) NOT NULL DEFAULT 'draft',
    remarks NVARCHAR(MAX) NULL,
    finance_remarks NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    submitted_at DATETIME2 NULL,
    decided_at DATETIME2 NULL,
    paid_at DATETIME2 NULL
);
CREATE INDEX IX_expense_claims_submitted_by ON dbo.expense_claims(submitted_by);
CREATE INDEX IX_expense_claims_status ON dbo.expense_claims(status);

CREATE TABLE dbo.expense_receipts (
    id NVARCHAR(64) NOT NULL PRIMARY KEY,
    claim_id NVARCHAR(64) NULL REFERENCES dbo.expense_claims(id),
    s3_key NVARCHAR(512) NOT NULL,
    content_type NVARCHAR(128) NOT NULL DEFAULT 'image/jpeg',
    ocr_raw_json NVARCHAR(MAX) NULL,
    ocr_vendor NVARCHAR(256) NULL,
    ocr_amount FLOAT NULL,
    ocr_date NVARCHAR(32) NULL,
    ocr_confidence FLOAT NULL,
    image_hash NVARCHAR(128) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX IX_expense_receipts_claim_id ON dbo.expense_receipts(claim_id);
CREATE INDEX IX_expense_receipts_image_hash ON dbo.expense_receipts(image_hash);

CREATE TABLE dbo.expense_claim_history (
    id NVARCHAR(64) NOT NULL PRIMARY KEY,
    claim_id NVARCHAR(64) NOT NULL REFERENCES dbo.expense_claims(id),
    actor_id NVARCHAR(64) NOT NULL,
    action NVARCHAR(32) NOT NULL,
    remarks NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE INDEX IX_expense_claim_history_claim_id ON dbo.expense_claim_history(claim_id);
GO

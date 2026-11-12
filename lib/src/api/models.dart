import '../utils/currency.dart';
import 'enums.dart';

/// Display name of a role. In an employee-advance company (Professional Signs / KSA) the
/// finance_manager role is the "Accounts Manager".
String roleLabelFor(String? role, {bool employeeAdvances = false}) {
  switch ((role ?? '').toLowerCase()) {
    case 'finance_manager':
      return employeeAdvances ? 'Accounts Manager' : 'Finance Manager';
    case 'accountant':
      return 'Accountant';
    case 'head_accountant':
      return 'Head of Accountant';
    case 'hod':
      return 'Head of Department';
    case 'admin':
      return 'Admin';
    case 'employee':
      return 'Employee';
    default:
      return role ?? '';
  }
}

class AuthUser {
  const AuthUser({
    required this.id,
    required this.displayName,
    required this.role,
    this.username,
    this.email,
    this.departmentId,
    this.departmentName,
    this.regionCode,
    this.allowedRegions = const [],
    this.pcaModel = 'department',
  });

  final int id;
  final String displayName;
  final String role;
  final String? username;
  final String? email;
  final int? departmentId;
  final String? departmentName;
  final String? regionCode;
  final List<String> allowedRegions;

  /// Petty cash model of the company signed in under: 'employee' = advances per employee
  /// and project (Professional Signs / KSA), 'department' = department pots (Dubai).
  final String pcaModel;

  UserRole get userRole => UserRoleX.fromJson(role);
  bool get isApprover => userRole.isApprover;
  bool get usesEmployeeAdvances => pcaModel == 'employee';

  /// Blue Rhine Contracting: petty cash per employee per site (OP code), no HODs.
  bool get usesSitePots => pcaModel == 'site';

  /// Role name as this company calls it: Professional Signs (KSA) calls the Finance Manager
  /// the "Accounts Manager".
  String get roleLabel => roleLabelFor(role, employeeAdvances: usesEmployeeAdvances);

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      id: (json['id'] as num).toInt(),
      displayName: (json['display_name'] ?? json['displayName'] ?? '') as String,
      role: (json['role'] as String? ?? 'employee').toLowerCase().trim(),
      username: json['username'] as String?,
      email: json['email'] as String?,
      departmentId: (json['department_id'] as num?)?.toInt(),
      departmentName: json['department_name'] as String?,
      regionCode: json['region_code'] as String?,
      allowedRegions: [
        for (final c in (json['allowed_regions'] as List? ?? const []))
          if (c is String && c.isNotEmpty) c,
      ],
      pcaModel: json['pca_model'] as String? ?? 'department',
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'display_name': displayName,
        'role': role,
        'username': username,
        'email': email,
        'department_id': departmentId,
        'department_name': departmentName,
        'region_code': regionCode,
        'allowed_regions': allowedRegions,
        'pca_model': pcaModel,
      };
}

class OcrResult {
  const OcrResult({
    required this.receiptId,
    required this.s3Key,
    required this.vendor,
    this.expenseType,
    this.amount,
    this.vatAmount,
    this.totalAmount,
    this.currency,
    required this.date,
    this.confidence,
    this.fieldConfidence,
    this.lowConfidenceFields,
    this.rawText,
    this.imageUrl,
    this.imageHash,
    this.duplicateWarning,
    this.ocrStatus,
    this.reconciliationMismatch = false,
    this.lineItems = const [],
    this.billNumber,
  });

  final int receiptId;
  final String s3Key;
  final String vendor;
  final String? expenseType;
  final double? amount;
  final double? vatAmount;
  final double? totalAmount;
  final String? currency;
  final String date;
  final double? confidence;
  final Map<String, double>? fieldConfidence;
  final List<String>? lowConfidenceFields;
  final String? rawText;
  final String? imageUrl;
  final String? imageHash;
  final DuplicateWarning? duplicateWarning;
  final String? ocrStatus;
  final bool reconciliationMismatch;
  final String? billNumber;

  /// Item rows the scan read off an itemised bill -- a suggestion for "Multiple items".
  final List<OcrLineItem> lineItems;

  bool get isPending => ocrStatus == 'pending';

  bool isLow(String field) =>
      (lowConfidenceFields ?? const <String>[]).contains(field);

  double? confidenceFor(String field) =>
      (fieldConfidence ?? const <String, double>{})[field];

  factory OcrResult.fromJson(Map<String, dynamic> json) {
    final rawConfidence = json['field_confidence'];
    final fieldConfidence = <String, double>{};
    if (rawConfidence is Map) {
      rawConfidence.forEach((key, value) {
        if (value is num) fieldConfidence[key.toString()] = value.toDouble();
      });
    }
    final rawLow = json['low_confidence_fields'];
    return OcrResult(
      receiptId: (json['receipt_id'] as num).toInt(),
      s3Key: json['s3_key'] as String,
      vendor: (json['vendor'] ?? '') as String,
      expenseType: json['expense_type'] as String?,
      amount: (json['amount'] as num?)?.toDouble(),
      vatAmount: (json['vat_amount'] as num?)?.toDouble(),
      totalAmount: (json['total_amount'] as num?)?.toDouble(),
      currency: json['currency'] as String?,
      date: (json['date'] ?? '') as String,
      confidence: (json['confidence'] as num?)?.toDouble(),
      fieldConfidence: fieldConfidence,
      lowConfidenceFields: rawLow is List ? rawLow.map((e) => e.toString()).toList() : const [],
      rawText: json['raw_text'] as String?,
      imageUrl: json['image_url'] as String?,
      imageHash: json['image_hash'] as String?,
      billNumber: json['bill_number'] as String?,
      duplicateWarning: json['duplicate_warning'] == null
          ? null
          : DuplicateWarning.fromJson(json['duplicate_warning'] as Map<String, dynamic>),
      ocrStatus: json['ocr_status'] as String?,
      reconciliationMismatch: json['reconciliation_mismatch'] == true,
      lineItems: (json['line_items'] as List?)
              ?.map((e) => OcrLineItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );
  }
}

class OcrLineItem {
  const OcrLineItem({required this.description, this.quantity, this.amount, this.confidence, this.vatPercent});

  final String description;
  final double? quantity;
  final double? amount;
  final double? confidence;
  final double? vatPercent;

  factory OcrLineItem.fromJson(Map<String, dynamic> json) {
    return OcrLineItem(
      description: (json['description'] ?? '') as String,
      quantity: (json['quantity'] as num?)?.toDouble(),
      amount: (json['amount'] as num?)?.toDouble(),
      confidence: (json['confidence'] as num?)?.toDouble(),
      vatPercent: (json['vat_percent'] as num?)?.toDouble(),
    );
  }
}

/// A saved item line on a "Multiple items" claim.
class ClaimLineItem {
  const ClaimLineItem({
    required this.lineNo,
    required this.description,
    required this.amount,
    this.quantity,
    this.categoryId,
    this.categoryName,
    this.opNumber,
    this.vatPercent,
    this.owningDepartmentId,
    this.owningDepartmentName,
    this.amountBase,
  });

  final int? owningDepartmentId;

  final int lineNo;
  /// [amount] converted into the company's base currency (set once the bill is submitted).
  final double? amountBase;
  final String description;
  final double? quantity;
  final double amount;
  final int? categoryId;
  final String? categoryName;
  final String? opNumber;
  final double? vatPercent;

  /// Set when this line belongs to another department than the employee's (its HOD
  /// approves it; for petty cash its fund pays for it).
  final String? owningDepartmentName;

  factory ClaimLineItem.fromJson(Map<String, dynamic> json) {
    return ClaimLineItem(
      lineNo: (json['line_no'] as num?)?.toInt() ?? 0,
      description: (json['description'] ?? '') as String,
      quantity: (json['quantity'] as num?)?.toDouble(),
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      categoryId: (json['category_id'] as num?)?.toInt(),
      categoryName: json['category_name'] as String?,
      opNumber: json['op_number'] as String?,
      vatPercent: (json['vat_percent'] as num?)?.toDouble(),
      owningDepartmentId: (json['owning_department_id'] as num?)?.toInt(),
      owningDepartmentName: json['owning_department_name'] as String?,
      amountBase: (json['amount_base'] as num?)?.toDouble(),
    );
  }
}

class DuplicateWarning {
  const DuplicateWarning({
    required this.reason,
    required this.message,
    this.existingClaimId,
  });

  final String reason;
  final String message;
  final int? existingClaimId;

  factory DuplicateWarning.fromJson(Map<String, dynamic> json) {
    return DuplicateWarning(
      reason: json['reason'] as String? ?? 'unknown',
      message: json['message'] as String? ?? 'Possible duplicate claim',
      existingClaimId: (json['existing_claim_id'] as num?)?.toInt(),
    );
  }
}

class ReceiptInfo {
  const ReceiptInfo({
    required this.id,
    required this.s3Key,
    this.contentType,
    this.ocrVendor,
    this.ocrAmount,
    this.ocrDate,
    this.ocrConfidence,
    this.imageHash,
    this.imageUrl,
    this.pageImageUrls = const [],
  });

  final int id;
  final String s3Key;
  final String? contentType;
  final String? ocrVendor;
  final double? ocrAmount;
  final String? ocrDate;
  final double? ocrConfidence;
  final String? imageHash;
  final String? imageUrl;

  /// Every page of the bill in order (page 1 first). Just [imageUrl] for one-page bills,
  /// old claims and list responses, which don't include `pages`.
  final List<String> pageImageUrls;

  factory ReceiptInfo.fromJson(Map<String, dynamic> json) {
    final imageUrl = json['image_url'] as String?;
    final pages = (json['pages'] as List?)
            ?.map((p) => (p as Map<String, dynamic>)['image_url'] as String?)
            .whereType<String>()
            .toList() ??
        const <String>[];
    return ReceiptInfo(
      id: (json['id'] as num).toInt(),
      s3Key: json['s3_key'] as String,
      contentType: json['content_type'] as String?,
      ocrVendor: json['ocr_vendor'] as String?,
      ocrAmount: (json['ocr_amount'] as num?)?.toDouble(),
      ocrDate: json['ocr_date'] as String?,
      ocrConfidence: (json['ocr_confidence'] as num?)?.toDouble(),
      imageHash: json['image_hash'] as String?,
      imageUrl: imageUrl,
      pageImageUrls: pages.isNotEmpty ? pages : [?imageUrl],
    );
  }
}

class ClaimHistoryItem {
  const ClaimHistoryItem({
    required this.id,
    required this.actorId,
    required this.action,
    this.actorName,
    this.stage,
    this.remarks,
    this.createdAt,
  });

  final int id;
  final int actorId;
  final String? actorName;
  final String action; // approve | dispute | reject | submitted | edited | paid
  final String? stage; // hod | department_hod | accountant | finance_manager | employee
  final String? remarks;
  final String? createdAt;

  factory ClaimHistoryItem.fromJson(Map<String, dynamic> json) {
    return ClaimHistoryItem(
      id: (json['id'] as num).toInt(),
      actorId: (json['actor_id'] as num).toInt(),
      actorName: json['actor_name'] as String?,
      action: json['action'] as String,
      stage: json['stage'] as String?,
      remarks: json['remarks'] as String?,
      createdAt: json['created_at'] as String?,
    );
  }
}

class ExpenseClaim {
  const ExpenseClaim({
    required this.id,
    required this.employeeId,
    required this.amount,
    required this.currency,
    this.exchangeRate = 1.0,
    required this.categoryId,
    required this.status,
    this.type = 'reimbursement',
    this.regionCode,
    this.employeeName,
    this.vendorName,
    this.categoryName,
    this.vatAmount = 0,
    this.totalAmount,
    this.billDate,
    this.projectId,
    this.opNumber,
    this.billNumber,
    this.remarks,
    this.currentStage,
    this.currentStageKey,
    this.disputeReturned = false,
    this.createdAt,
    this.updatedAt,
    this.submittedAt,
    this.decidedAt,
    this.paidAt,
    this.receipt,
    this.history,
    this.duplicateWarning,
    this.duplicateFlag = false,
    this.stageSequence = const [],
    this.stageLabels = const {},
    this.lineItems = const [],
    this.baseCurrency,
    this.exchangeRateDate,
    this.totalAmountBase,
    this.paymentStatus = 'not_applicable',
    this.payment,
    this.payableAmount,
    this.payableCurrency,
    this.journalType,
    this.journalReference,
    this.journalStage,
    this.paysByProcess = false,
  });

  /// Professional Signs: payment is recorded as PDF section 7 Process 1 (cash withdrawal from
  /// bank) or Process 2 (direct payment by Accounts), and approved petty cash is paid too.
  final bool paysByProcess;

  /// Expense journal Accounts booked for this bill (Professional Signs: EJV or EJVB) and
  /// its ERP number.
  final String? journalType;
  final String? journalReference;

  /// The approval stage that must record the journal for this company (null = none).
  final String? journalStage;

  /// Company's base currency the bill was converted into at submit.
  final String? baseCurrency;
  /// Day of the rate used (locked at first submit).
  final String? exchangeRateDate;
  final double? totalAmountBase;
  /// not_applicable (petty cash / not yet approved) | unpaid | paid.
  final String paymentStatus;
  final PaymentRecord? payment;
  /// Payments list only: what the employee is owed, in the company's base currency.
  final double? payableAmount;
  final String? payableCurrency;

  bool get isConverted =>
      baseCurrency != null && totalAmountBase != null && baseCurrency!.toUpperCase() != currency.toUpperCase();

  final int id;
  final int employeeId;
  final String type;
  final String? regionCode;
  final String? employeeName;
  final String? vendorName;
  final double amount;
  final String currency;
  /// 1 bill-currency unit = this many of the region's base currency, frozen at submit.
  final double exchangeRate;
  final double vatAmount;
  final double? totalAmount;
  final String? billDate;
  final int categoryId;
  final String? categoryName;
  final int? projectId;
  final String? opNumber;
  final String? billNumber;
  final String status;
  /// Base stage name (hod | department_hod | accountant | finance_manager) — use for
  /// role/queue checks.
  final String? currentStage;

  /// Which step exactly: `department_hod:<id>` names the department (a bill can need
  /// several department HODs). Matches [stageSequence], [stageLabels] and history stages.
  final String? currentStageKey;
  final bool disputeReturned;
  final String? remarks;
  final String? createdAt;
  final String? updatedAt;
  final String? submittedAt;
  final String? decidedAt;
  final String? paidAt;
  final ReceiptInfo? receipt;
  final List<ClaimHistoryItem>? history;
  final DuplicateWarning? duplicateWarning;
  /// Persisted at submission time (same employee + vendor + amount + date) -- unlike
  /// [duplicateWarning], this is present on list endpoints too.
  final bool duplicateFlag;
  final List<String> stageSequence;

  /// Per-claim names so a cross-dept bill shows "Sales HOD" then "IT HOD"
  /// instead of the generic "HOD" / "Department HOD".
  final Map<String, String> stageLabels;

  static const _fallbackStageLabels = {
    'hod': 'HOD',
    'department_hod': 'Department HOD',
    'accountant': 'Accountant',
    'head_accountant': 'Head of Accountant',
    'finance_manager': 'Finance Manager',
    'employee': 'Employee',
  };

  /// Label for a workflow stage on this claim (department names when known).
  String stageLabel(String? stage) {
    if (stage == null || stage.isEmpty) return 'None';
    return stageLabels[stage] ?? _fallbackStageLabels[stage.split(':').first] ?? stage;
  }

  /// Label of the step the claim is waiting at, with the department name for
  /// cross-department HOD steps (e.g. "IT HOD").
  String get currentStageLabel => stageLabel(currentStageKey ?? currentStage);

  /// Non-empty for "Multiple items" bills; the total is the sum of these.
  final List<ClaimLineItem> lineItems;
  bool get isMultiItem => lineItems.isNotEmpty;

  /// Backward-compat display helper — old UI code refers to "vendor".
  String get vendor => vendorName ?? '';

  /// Backward-compat display helper — old UI code refers to "category".
  String get category => categoryName ?? '';

  /// Falls back to "employee #N" only if the display name genuinely isn't
  /// available (e.g. an orphaned employee_id) — never shown otherwise.
  String get employeeDisplay => employeeName ?? 'employee #$employeeId';

  /// Most recent dispute/reject history entry — the authoritative source for
  /// "why was this sent back," since `remarks` alone can be stale (it's also
  /// written by unrelated edit paths).
  ClaimHistoryItem? get lastReturnEntry {
    final h = history;
    if (h == null) return null;
    for (final entry in h.reversed) {
      if (entry.action == 'dispute' || entry.action == 'reject') return entry;
    }
    return null;
  }

  factory ExpenseClaim.fromJson(Map<String, dynamic> json) {
    return ExpenseClaim(
      id: (json['id'] as num).toInt(),
      employeeId: (json['employee_id'] as num?)?.toInt() ?? 0,
      type: json['type'] as String? ?? 'reimbursement',
      regionCode: json['region_code'] as String?,
      employeeName: json['employee_name'] as String?,
      vendorName: json['vendor_name'] as String?,
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      currency: json['currency'] as String? ?? 'AED',
      exchangeRate: (json['exchange_rate'] as num?)?.toDouble() ?? 1.0,
      vatAmount: (json['vat_amount'] as num?)?.toDouble() ?? 0,
      totalAmount: (json['total_amount'] as num?)?.toDouble(),
      billDate: json['bill_date'] as String?,
      categoryId: (json['category_id'] as num?)?.toInt() ?? 0,
      categoryName: json['category_name'] as String?,
      projectId: (json['project_id'] as num?)?.toInt(),
      opNumber: json['op_number'] as String?,
      billNumber: json['bill_number'] as String?,
      status: json['status'] as String? ?? 'draft',
      currentStage: json['current_stage'] as String?,
      currentStageKey: json['current_stage_key'] as String? ?? json['current_stage'] as String?,
      disputeReturned: json['dispute_returned'] as bool? ?? false,
      remarks: json['remarks'] as String?,
      createdAt: json['created_at'] as String?,
      updatedAt: json['updated_at'] as String?,
      submittedAt: json['submitted_at'] as String?,
      decidedAt: json['decided_at'] as String?,
      paidAt: json['paid_at'] as String?,
      receipt: json['receipt'] == null
          ? null
          : ReceiptInfo.fromJson(json['receipt'] as Map<String, dynamic>),
      history: (json['history'] as List?)
          ?.map((e) => ClaimHistoryItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      duplicateWarning: json['duplicate_warning'] == null
          ? null
          : DuplicateWarning.fromJson(json['duplicate_warning'] as Map<String, dynamic>),
      duplicateFlag: json['duplicate_flag'] as bool? ?? false,
      stageSequence: (json['stage_sequence'] as List?)?.map((e) => e as String).toList() ?? const [],
      stageLabels: {
        if (json['stage_labels'] is Map)
          for (final e in (json['stage_labels'] as Map).entries)
            e.key.toString(): e.value.toString(),
      },
      lineItems: (json['line_items'] as List?)
              ?.map((e) => ClaimLineItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      baseCurrency: json['base_currency'] as String?,
      exchangeRateDate: json['exchange_rate_date'] as String?,
      totalAmountBase: (json['total_amount_base'] as num?)?.toDouble(),
      paymentStatus: json['payment_status'] as String? ?? 'not_applicable',
      payment: json['payment'] is Map
          ? PaymentRecord.fromJson(Map<String, dynamic>.from(json['payment'] as Map))
          : null,
      payableAmount: (json['payable_amount'] as num?)?.toDouble(),
      payableCurrency: json['payable_currency'] as String?,
      journalType: json['journal_type'] as String?,
      journalReference: json['journal_reference'] as String?,
      journalStage: json['journal_stage'] as String?,
      paysByProcess: json['pays_by_process'] == true,
    );
  }
}

class CategoryRef {
  const CategoryRef({
    required this.id,
    required this.name,
    this.nameAr,
    this.owningDepartmentId,
    this.owningDepartmentName,
  });

  final int id;
  final String name;
  final String? nameAr;

  /// Department that owns this category (e.g. IT Equipment → IT). Items in it go to
  /// that department's HOD and, for petty cash, come out of that department's fund.
  final int? owningDepartmentId;
  final String? owningDepartmentName;

  /// The other department this category belongs to, or null when it's the employee's own
  /// (or not owned by any department).
  String? otherDepartmentFor(int? ownDepartmentId) =>
      owningDepartmentId != null && owningDepartmentId != ownDepartmentId ? owningDepartmentName : null;

  factory CategoryRef.fromJson(Map<String, dynamic> json) {
    return CategoryRef(
      id: (json['id'] as num).toInt(),
      name: json['name'] as String,
      nameAr: json['name_ar'] as String?,
      owningDepartmentId: (json['owning_department_id'] as num?)?.toInt(),
      owningDepartmentName: json['owning_department_name'] as String?,
    );
  }
}

class ProjectRef {
  const ProjectRef({required this.id, required this.name, this.opNumber});

  final int id;
  final String name;
  final String? opNumber;

  factory ProjectRef.fromJson(Map<String, dynamic> json) {
    return ProjectRef(
      id: (json['id'] as num).toInt(),
      name: json['name'] as String,
      opNumber: json['op_number'] as String?,
    );
  }
}


class OpportunityResult {
  const OpportunityResult({
    required this.opCode,
    required this.name,
    this.buCode,
    this.salesPerson,
  });

  final String opCode;
  final String name;
  final String? buCode;
  final String? salesPerson;

  factory OpportunityResult.fromJson(Map<String, dynamic> json) {
    return OpportunityResult(
      opCode:      json['op_code'] as String,
      name:        json['name'] as String,
      buCode:      json['bu_code'] as String?,
      salesPerson: json['sales_person'] as String?,
    );
  }
}

/// One workflow event from `GET /api/admin/activity` (web dashboard feed).
class ActivityItem {
  const ActivityItem({
    required this.id,
    required this.transactionId,
    required this.action,
    this.stage,
    this.comment,
    this.actorName,
    this.employeeName,
    this.vendorName,
    this.currency,
    this.totalAmount,
    this.createdAt,
  });

  final int id;
  final int transactionId;
  final String action;
  final String? stage;
  final String? comment;
  final String? actorName;
  final String? employeeName;
  final String? vendorName;
  final String? currency;
  final double? totalAmount;
  final String? createdAt;

  factory ActivityItem.fromJson(Map<String, dynamic> json) {
    return ActivityItem(
      id: (json['id'] as num).toInt(),
      transactionId: (json['transaction_id'] as num).toInt(),
      action: json['action'] as String? ?? '',
      stage: json['stage'] as String?,
      comment: json['comment'] as String?,
      actorName: json['actor_name'] as String?,
      employeeName: json['employee_name'] as String?,
      vendorName: json['vendor_name'] as String?,
      currency: json['currency'] as String?,
      totalAmount: (json['total_amount'] as num?)?.toDouble(),
      createdAt: json['created_at'] as String?,
    );
  }
}

class ExchangeRateQuote {
  const ExchangeRateQuote({
    required this.rate,
    required this.asOf,
    required this.billCurrency,
    required this.baseCurrency,
    this.source,
  });

  final double rate;
  final String asOf;
  final String billCurrency;
  final String baseCurrency;
  final String? source;

  factory ExchangeRateQuote.fromJson(Map<String, dynamic> json) {
    return ExchangeRateQuote(
      rate: (json['rate'] as num).toDouble(),
      asOf: json['as_of'] as String? ?? '',
      billCurrency: json['bill_currency'] as String? ?? '',
      baseCurrency: json['base_currency'] as String? ?? '',
      source: json['source'] as String?,
    );
  }
}

class RegionConfig {
  const RegionConfig({
    required this.id,
    required this.regionCode,
    required this.regionName,
    this.companyName,
    this.logoUrl,
    this.baseCurrency,
    this.pcaModel = 'department',
  });

  final int id;
  final String regionCode;
  final String regionName;
  final String? companyName;
  final String? logoUrl;

  /// Currency this company keeps its books (and petty cash funds) in.
  final String? baseCurrency;

  /// 'employee' = one advance per employee (Professional Signs), 'site' = pots per employee
  /// per site (Blue Rhine Contracting), else 'department'.
  final String pcaModel;
  bool get usesEmployeeAdvances => pcaModel == 'employee';
  bool get usesSitePots => pcaModel == 'site';

  factory RegionConfig.fromJson(Map<String, dynamic> json) {
    final region = RegionConfig(
      id: (json['id'] as num).toInt(),
      regionCode: json['region_code'] as String? ?? '',
      regionName: json['region_name'] as String? ?? '',
      companyName: json['company_name'] as String?,
      logoUrl: json['logo_url'] as String?,
      baseCurrency: json['base_currency'] as String?,
      pcaModel: json['pca_model'] as String? ?? 'department',
    );
    rememberRegionBaseCurrency(region.regionCode, region.baseCurrency);
    return region;
  }
}

/// How an approved reimbursement was paid (one per claim).
class PaymentRecord {
  const PaymentRecord({
    required this.amount,
    required this.currency,
    required this.method,
    required this.methodLabel,
    required this.reference,
    this.paymentDate,
    this.paidByName,
    this.remarks,
  });

  final double amount;
  final String currency;
  final String method;
  final String methodLabel;
  final String reference;
  final String? paymentDate;
  final String? paidByName;
  final String? remarks;

  factory PaymentRecord.fromJson(Map<String, dynamic> json) {
    return PaymentRecord(
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      currency: json['currency'] as String? ?? '',
      method: json['payment_method'] as String? ?? '',
      methodLabel: json['payment_method_label'] as String? ?? json['payment_method'] as String? ?? '',
      reference: json['payment_reference'] as String? ?? '',
      paymentDate: json['payment_date'] as String?,
      paidByName: json['paid_by_name'] as String?,
      remarks: json['remarks'] as String?,
    );
  }
}

/// `GET /api/payments` — one page of claims plus totals of every match per currency.
class PaymentsPage {
  const PaymentsPage({required this.items, required this.total, required this.totals});

  final List<ExpenseClaim> items;
  final int total;
  final Map<String, double> totals;

  factory PaymentsPage.fromJson(Map<String, dynamic> json) {
    return PaymentsPage(
      items: (json['items'] as List? ?? const [])
          .map((e) => ExpenseClaim.fromJson(e as Map<String, dynamic>))
          .toList(),
      total: (json['total'] as num?)?.toInt() ?? 0,
      totals: {
        if (json['totals'] is Map)
          for (final e in (json['totals'] as Map).entries)
            e.key.toString(): (e.value as num).toDouble(),
      },
    );
  }
}

class OrgUserPage {
  const OrgUserPage({
    required this.items,
    required this.total,
    required this.limit,
    required this.offset,
  });

  final List<OrgUser> items;
  final int total;
  final int limit;
  final int offset;

  bool get hasMore => offset + items.length < total;

  factory OrgUserPage.fromJson(Map<String, dynamic> json) {
    return OrgUserPage(
      items: [
        for (final row in (json['items'] as List? ?? const []))
          if (row is Map) OrgUser.fromJson(Map<String, dynamic>.from(row)),
      ],
      total: (json['total'] as num?)?.toInt() ?? 0,
      limit: (json['limit'] as num?)?.toInt() ?? 25,
      offset: (json['offset'] as num?)?.toInt() ?? 0,
    );
  }
}

class OrgUser {
  const OrgUser({
    required this.id,
    required this.displayName,
    this.employeeId,
    this.username,
    this.email,
    this.role,
    this.erpRole,
    this.departmentName,
    this.homeRegionCode,
    this.regionCodes = const [],
    this.hasAppLogin = false,
  });

  final int id;
  final String displayName;
  final int? employeeId;
  final String? username;
  final String? email;
  final String? role;
  final String? erpRole;
  final String? departmentName;
  final String? homeRegionCode;
  final List<String> regionCodes;
  final bool hasAppLogin;

  bool belongsTo(String regionCode) {
    final code = regionCode.toUpperCase();
    if ((homeRegionCode ?? '').toUpperCase() == code) return true;
    return regionCodes.any((c) => c.toUpperCase() == code);
  }

  bool isHomeCompany(String regionCode) =>
      (homeRegionCode ?? '').toUpperCase() == regionCode.toUpperCase();

  factory OrgUser.fromJson(Map<String, dynamic> json) {
    return OrgUser(
      id: (json['id'] as num).toInt(),
      displayName: json['display_name'] as String? ?? '',
      employeeId: (json['employee_id'] as num?)?.toInt(),
      username: json['username'] as String?,
      email: json['email'] as String?,
      role: json['role'] as String?,
      erpRole: json['erp_role'] as String?,
      departmentName: json['department_name'] as String?,
      homeRegionCode: json['home_region_code'] as String?,
      regionCodes: [
        for (final c in (json['region_codes'] as List? ?? const []))
          if (c is String) c,
      ],
      hasAppLogin: json['has_app_login'] == true,
    );
  }
}

class PettyCashFund {
  const PettyCashFund({
    required this.id,
    required this.ownerType,
    required this.currency,
    required this.openingBalance,
    required this.remaining,
    this.regionId,
    this.regionCode,
    this.companyName,
    this.departmentId,
    this.departmentName,
    this.employeeId,
    this.employeeName,
    this.label,
    this.credited = 0,
    this.spent = 0,
    this.pendingTopup = 0,
    this.unreplenishedSpend = 0,
    this.pendingBills = 0,
    this.opNumber,
    this.opName,
    this.spendLimit,
    double? uncommitted,
  }) : _uncommitted = uncommitted;

  /// Employee advance with a hard limit (Professional Signs: 50% of the PCA): the most that
  /// bills not yet topped up may use. Null = no cap beyond the PCA.
  final double? spendLimit;

  /// Employee advance (Professional Signs): the project it is for. Null on department pots.
  final String? opNumber;
  final String? opName;

  /// "OP-2201 Riyadh Mall", or null when this isn't a project advance.
  String? get projectLabel {
    final op = (opNumber ?? '').trim();
    if (op.isEmpty) return null;
    final name = (opName ?? '').trim();
    return name.isEmpty ? op : '$op $name';
  }

  final int id;
  final String ownerType;
  final String currency;
  final double openingBalance;
  final double remaining;
  final int? regionId;
  final String? regionCode;
  final String? companyName;
  final int? departmentId;
  final String? departmentName;
  final int? employeeId;
  final String? employeeName;
  final String? label;
  final double credited;
  final double spent;
  final double pendingTopup;
  final double unreplenishedSpend;
  /// Petty-cash bills submitted but not yet finally approved -- reserved, not yet deducted.
  final double pendingBills;
  final double? _uncommitted;

  double get approvedLimit => openingBalance;
  double get available => remaining;
  /// What a new bill can still use: available minus bills awaiting approval.
  double get uncommitted => _uncommitted ?? (remaining - pendingBills);

  factory PettyCashFund.fromJson(Map<String, dynamic> json) {
    return PettyCashFund(
      id: (json['id'] as num).toInt(),
      ownerType: json['owner_type'] as String? ?? '',
      currency: json['currency'] as String? ?? 'AED',
      openingBalance: (json['approved_limit'] as num?)?.toDouble() ??
          (json['opening_balance'] as num?)?.toDouble() ??
          0,
      remaining: (json['available'] as num?)?.toDouble() ?? (json['remaining'] as num?)?.toDouble() ?? 0,
      regionId: (json['region_id'] as num?)?.toInt(),
      regionCode: json['region_code'] as String?,
      companyName: json['company_name'] as String? ?? json['region_name'] as String?,
      departmentId: (json['department_id'] as num?)?.toInt(),
      departmentName: json['department_name'] as String?,
      employeeId: (json['employee_id'] as num?)?.toInt(),
      employeeName: json['employee_name'] as String?,
      label: json['label'] as String?,
      credited: (json['replenished'] as num?)?.toDouble() ?? (json['credited'] as num?)?.toDouble() ?? 0,
      spent: (json['spent'] as num?)?.toDouble() ?? 0,
      pendingTopup: (json['pending_topup'] as num?)?.toDouble() ?? 0,
      unreplenishedSpend: (json['unreplenished_spend'] as num?)?.toDouble() ?? 0,
      pendingBills: (json['pending_bills'] as num?)?.toDouble() ?? 0,
      uncommitted: (json['uncommitted'] as num?)?.toDouble(),
      spendLimit: (json['spend_limit'] as num?)?.toDouble(),
      opNumber: json['op_number'] as String?,
      opName: json['op_name'] as String?,
    );
  }
}

class DepartmentFund {
  const DepartmentFund({
    required this.departmentId,
    required this.departmentName,
    this.fund,
  });

  final int departmentId;
  final String departmentName;
  final PettyCashFund? fund;

  factory DepartmentFund.fromJson(Map<String, dynamic> json) {
    return DepartmentFund(
      departmentId: (json['department_id'] as num).toInt(),
      departmentName: json['department_name'] as String? ?? '',
      fund: json['fund'] is Map
          ? PettyCashFund.fromJson(Map<String, dynamic>.from(json['fund'] as Map))
          : null,
    );
  }
}

class ReplenishableBill {
  const ReplenishableBill({
    required this.id,
    required this.amount,
    this.billTotal,
    this.billDate,
    this.currency,
  });

  final int id;

  /// This fund's part of the bill — only the IT lines of a Sales bill, for the IT fund.
  final double amount;
  final double? billTotal;
  final String? billDate;
  final String? currency;

  bool get isPartOfBill => billTotal != null && (billTotal! - amount).abs() > 0.004;

  factory ReplenishableBill.fromJson(Map<String, dynamic> json) {
    return ReplenishableBill(
      id: (json['id'] as num).toInt(),
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      billTotal: (json['bill_total'] as num?)?.toDouble(),
      billDate: json['bill_date'] as String?,
      currency: json['currency'] as String?,
    );
  }
}

class TopupRequest {
  const TopupRequest({
    required this.id,
    required this.amount,
    required this.status,
    this.remarks,
    this.requesterName,
    this.fund,
    this.paymentReference,
    this.transactionIds = const [],
    this.departmentName,
    this.history = const [],
    this.kind = 'topup',
    this.employeeId,
    this.employeeName,
    this.paymentSource,
    this.paymentMethod,
    this.paymentDate,
    this.paidByName,
    this.regionCode,
  });

  /// 'advance' (giving / raising an employee's advance) or 'topup' (replenishing bills).
  final String kind;
  final int? employeeId;
  final String? employeeName;

  /// Where the money came from: 'bank' or 'accounts_petty_cash' (employee advances).
  final String? paymentSource;
  final String? paymentMethod;
  final String? paymentDate;
  final String? paidByName;
  final String? regionCode;

  bool get isAdvance => kind == 'advance';

  final int id;
  final double amount;
  final String status;
  final String? remarks;
  final String? requesterName;
  final PettyCashFund? fund;
  final String? paymentReference;
  final List<int> transactionIds;
  final String? departmentName;
  /// Audit trail, oldest first: requested, verified / returned, approved / rejected.
  final List<TopupHistoryEntry> history;

  /// Why Accounts sent it back (latest "returned" step), if it was.
  String? get returnReason {
    for (final h in history.reversed) {
      if (h.action == 'returned') return h.comment;
    }
    return null;
  }

  factory TopupRequest.fromJson(Map<String, dynamic> json) {
    return TopupRequest(
      id: (json['id'] as num).toInt(),
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      status: json['status'] as String? ?? '',
      remarks: json['remarks'] as String?,
      requesterName: json['requester_name'] as String?,
      fund: json['fund'] is Map
          ? PettyCashFund.fromJson(Map<String, dynamic>.from(json['fund'] as Map))
          : null,
      paymentReference: json['payment_reference'] as String?,
      transactionIds: [
        for (final id in (json['transaction_ids'] as List? ?? const []))
          if (id is num) id.toInt(),
      ],
      departmentName: json['department_name'] as String?,
      history: [
        for (final row in (json['history'] as List? ?? const []))
          if (row is Map) TopupHistoryEntry.fromJson(Map<String, dynamic>.from(row)),
      ],
      kind: json['kind'] as String? ?? 'topup',
      employeeId: (json['employee_id'] as num?)?.toInt(),
      employeeName: json['employee_name'] as String?,
      paymentSource: json['payment_source'] as String?,
      paymentMethod: json['payment_method'] as String?,
      paymentDate: json['payment_date'] as String?,
      paidByName: json['paid_by_name'] as String?,
      regionCode: json['region_code'] as String?,
    );
  }
}

/// Money figures shared by every row of the advances report (`GET /api/pca/summary`).
class PcaFigures {
  const PcaFigures({
    this.advance = 0,
    this.advanceWaiting = 0,
    this.spent = 0,
    this.unreplenishedSpend = 0,
    this.pendingBills = 0,
    this.pendingTopup = 0,
    this.available = 0,
  });

  /// Advance paid out so far.
  final double advance;

  /// Proposed or approved, not yet paid.
  final double advanceWaiting;
  final double spent;

  /// Approved bills not yet topped up.
  final double unreplenishedSpend;

  /// Bills still in approval (reserved).
  final double pendingBills;
  final double pendingTopup;
  final double available;

  factory PcaFigures.fromJson(Map<String, dynamic> json) {
    double n(String key) => (json[key] as num?)?.toDouble() ?? 0;
    return PcaFigures(
      advance: n('advance'),
      advanceWaiting: n('advance_waiting'),
      spent: n('spent'),
      unreplenishedSpend: n('unreplenished_spend'),
      pendingBills: n('pending_bills'),
      pendingTopup: n('pending_topup'),
      available: n('available'),
    );
  }
}

/// One employee's advance for one project, inside a report group.
class PcaMember {
  const PcaMember({
    required this.figures,
    this.fundId,
    this.employeeId,
    this.employeeName,
    this.departmentName,
    this.opNumber,
    this.opName,
    this.advances = const [],
  });

  final PcaFigures figures;
  final int? fundId;
  final int? employeeId;
  final String? employeeName;
  final String? departmentName;
  final String? opNumber;
  final String? opName;

  /// Department view only: this employee's advances, one per project.
  final List<PcaMember> advances;

  factory PcaMember.fromJson(Map<String, dynamic> json) {
    return PcaMember(
      figures: PcaFigures.fromJson(json),
      fundId: (json['fund_id'] as num?)?.toInt(),
      employeeId: (json['employee_id'] as num?)?.toInt(),
      employeeName: json['employee_name'] as String?,
      departmentName: json['department_name'] as String?,
      opNumber: json['op_number'] as String?,
      opName: json['op_name'] as String?,
      advances: [
        for (final row in (json['advances'] as List? ?? const []))
          if (row is Map) PcaMember.fromJson(Map<String, dynamic>.from(row)),
      ],
    );
  }
}

/// A department or a project in the advances report, with the employees in it.
class PcaGroup {
  const PcaGroup({
    required this.title,
    required this.figures,
    required this.employeeCount,
    required this.advanceCount,
    required this.employees,
    this.subtitle,
  });

  final String title;
  final String? subtitle;
  final PcaFigures figures;
  final int employeeCount;
  final int advanceCount;
  final List<PcaMember> employees;

  factory PcaGroup.fromJson(Map<String, dynamic> json, {required bool project}) {
    return PcaGroup(
      title: project
          ? (json['op_number'] as String? ?? 'No project')
          : (json['department_name'] as String? ?? 'No department'),
      subtitle: project ? json['op_name'] as String? : null,
      figures: PcaFigures.fromJson(json),
      employeeCount: (json['employee_count'] as num?)?.toInt() ?? 0,
      advanceCount: (json['advance_count'] as num?)?.toInt() ?? 0,
      employees: [
        for (final row in (json['employees'] as List? ?? const []))
          if (row is Map) PcaMember.fromJson(Map<String, dynamic>.from(row)),
      ],
    );
  }
}

/// `GET /api/pca/summary`: one company's employee advances by department and by project.
class PcaSummary {
  const PcaSummary({
    required this.currency,
    required this.totals,
    required this.employeeCount,
    required this.advanceCount,
    required this.projectCount,
    required this.byDepartment,
    required this.byProject,
    this.companyName,
  });

  final String currency;
  final String? companyName;
  final PcaFigures totals;
  final int employeeCount;
  final int advanceCount;
  final int projectCount;
  final List<PcaGroup> byDepartment;
  final List<PcaGroup> byProject;

  factory PcaSummary.fromJson(Map<String, dynamic> json) {
    final totals = Map<String, dynamic>.from(json['totals'] as Map? ?? const {});
    return PcaSummary(
      currency: json['currency'] as String? ?? '',
      companyName: json['company_name'] as String?,
      totals: PcaFigures.fromJson(totals),
      employeeCount: (totals['employee_count'] as num?)?.toInt() ?? 0,
      advanceCount: (totals['advance_count'] as num?)?.toInt() ?? 0,
      projectCount: (totals['project_count'] as num?)?.toInt() ?? 0,
      byDepartment: [
        for (final row in (json['by_department'] as List? ?? const []))
          if (row is Map) PcaGroup.fromJson(Map<String, dynamic>.from(row), project: false),
      ],
      byProject: [
        for (final row in (json['by_project'] as List? ?? const []))
          if (row is Map) PcaGroup.fromJson(Map<String, dynamic>.from(row), project: true),
      ],
    );
  }
}

/// A department on the Employees tab (`GET /api/pca/departments`): counts only, loads fast.
class PcaDepartment {
  const PcaDepartment({
    required this.departmentId,
    required this.name,
    required this.employeeCount,
    required this.withPettyCash,
    required this.notSet,
    required this.totalLimit,
  });

  /// 0 = people with no department.
  final int departmentId;
  final String name;
  final int employeeCount;
  final int withPettyCash;
  final int notSet;
  final double totalLimit;

  factory PcaDepartment.fromJson(Map<String, dynamic> json) => PcaDepartment(
        departmentId: (json['department_id'] as num?)?.toInt() ?? 0,
        name: json['department_name'] as String? ?? 'No department',
        employeeCount: (json['employee_count'] as num?)?.toInt() ?? 0,
        withPettyCash: (json['with_petty_cash'] as num?)?.toInt() ?? 0,
        notSet: (json['not_set'] as num?)?.toInt() ?? 0,
        totalLimit: (json['total_limit'] as num?)?.toDouble() ?? 0,
      );
}

class PcaDepartments {
  const PcaDepartments({required this.currency, required this.departments});

  final String currency;
  final List<PcaDepartment> departments;

  factory PcaDepartments.fromJson(Map<String, dynamic> json) => PcaDepartments(
        currency: json['currency'] as String? ?? '',
        departments: [
          for (final row in (json['departments'] as List? ?? const []))
            if (row is Map) PcaDepartment.fromJson(Map<String, dynamic>.from(row)),
        ],
      );
}

/// One department's employees with their petty cash figures
/// (`GET /api/pca/departments/{id}/employees`).
class PcaDepartmentEmployees {
  const PcaDepartmentEmployees({required this.currency, required this.name, required this.employees});

  final String currency;
  final String name;
  final List<PcaMember> employees;

  factory PcaDepartmentEmployees.fromJson(Map<String, dynamic> json) => PcaDepartmentEmployees(
        currency: json['currency'] as String? ?? '',
        name: json['department_name'] as String? ?? 'No department',
        employees: [
          for (final row in (json['employees'] as List? ?? const []))
            if (row is Map) PcaMember.fromJson(Map<String, dynamic>.from(row)),
        ],
      );
}

/// Someone an HOD (or Admin) may propose an advance for (`GET /api/pca/staff`).
class PcaStaff {
  const PcaStaff({required this.id, required this.displayName, this.departmentName, this.advance = 0});

  final int id;
  final String displayName;
  final String? departmentName;

  /// Current petty cash amount; 0 = not set yet.
  final double advance;

  factory PcaStaff.fromJson(Map<String, dynamic> json) => PcaStaff(
        id: (json['id'] as num).toInt(),
        displayName: json['display_name'] as String? ?? '',
        departmentName: json['department_name'] as String?,
        advance: (json['advance'] as num?)?.toDouble() ?? 0,
      );
}

/// One movement on the Accounts Department's petty cash.
class AccountsCashEntry {
  const AccountsCashEntry({
    required this.id,
    required this.kind,
    required this.amount,
    this.transactionId,
    this.topupId,
    this.employeeName,
    this.reference,
    this.date,
    this.remarks,
    this.actorName,
  });

  final int id;

  /// payout (Process 2 payment) | refill (from the bank) | set (Admin changed the amount).
  final String kind;
  final double amount;
  final int? transactionId;
  final int? topupId;
  final String? employeeName;
  final String? reference;
  final DateTime? date;
  final String? remarks;
  final String? actorName;

  factory AccountsCashEntry.fromJson(Map<String, dynamic> json) {
    final date = json['date'] as String?;
    return AccountsCashEntry(
      id: (json['id'] as num).toInt(),
      kind: json['kind'] as String? ?? '',
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      transactionId: (json['transaction_id'] as num?)?.toInt(),
      topupId: (json['topup_id'] as num?)?.toInt(),
      employeeName: json['employee_name'] as String?,
      reference: json['reference'] as String?,
      date: date == null ? null : DateTime.tryParse(date),
      remarks: json['remarks'] as String?,
      actorName: json['actor_name'] as String?,
    );
  }
}

/// `GET /api/pca/accounts-cash`: the Accounts Department's own petty cash (Professional Signs,
/// PCA PDF section 6). Process 2 payments take from it; the Accounts Manager refills it.
class AccountsCash {
  const AccountsCash({
    required this.regionId,
    required this.currency,
    required this.configured,
    required this.limit,
    required this.paidOut,
    required this.refilled,
    required this.toRefill,
    required this.available,
    required this.low,
    required this.canSet,
    required this.canRefill,
    required this.entries,
  });

  final int regionId;
  final String currency;
  final bool configured;
  final double limit;
  final double paidOut;
  final double refilled;
  final double toRefill;
  final double available;
  final bool low;
  final bool canSet;
  final bool canRefill;
  final List<AccountsCashEntry> entries;

  factory AccountsCash.fromJson(Map<String, dynamic> json) {
    double n(String key) => (json[key] as num?)?.toDouble() ?? 0;
    return AccountsCash(
      regionId: (json['region_id'] as num?)?.toInt() ?? 0,
      currency: json['currency'] as String? ?? '',
      configured: json['configured'] as bool? ?? false,
      limit: n('limit'),
      paidOut: n('paid_out'),
      refilled: n('refilled'),
      toRefill: n('to_refill'),
      available: n('available'),
      low: json['low'] as bool? ?? false,
      canSet: json['can_set'] as bool? ?? false,
      canRefill: json['can_refill'] as bool? ?? false,
      entries: [
        for (final row in (json['entries'] as List? ?? const []))
          if (row is Map) AccountsCashEntry.fromJson(Map<String, dynamic>.from(row)),
      ],
    );
  }
}

class TopupHistoryEntry {
  const TopupHistoryEntry({required this.action, this.actorName, this.comment, this.at});

  final String action; // requested | verified | returned | approved | rejected
  final String? actorName;
  final String? comment;
  final DateTime? at;

  factory TopupHistoryEntry.fromJson(Map<String, dynamic> json) {
    final at = json['at'] as String?;
    return TopupHistoryEntry(
      action: json['action'] as String? ?? '',
      actorName: json['actor_name'] as String?,
      comment: json['comment'] as String?,
      at: at == null ? null : DateTime.tryParse(at),
    );
  }
}

import '../utils/currency.dart';
import 'enums.dart';

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

  UserRole get userRole => UserRoleX.fromJson(role);
  bool get isApprover => userRole.isApprover;

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
    this.vendorUnmatched = false,
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
  });

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
  /// True when the vendor text (typed or OCR'd) didn't match any known vendor —
  /// vendorId stays null and vendorName falls back to the raw, unmatched text.
  final bool vendorUnmatched;
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
      vendorUnmatched: json['vendor_unmatched'] as bool? ?? false,
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

class VendorRef {
  const VendorRef({required this.id, required this.name});

  final int id;
  final String name;

  factory VendorRef.fromJson(Map<String, dynamic> json) {
    return VendorRef(
      id: (json['id'] as num).toInt(),
      name: json['name'] as String,
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
  });

  final int id;
  final String regionCode;
  final String regionName;
  final String? companyName;
  final String? logoUrl;

  /// Currency this company keeps its books (and petty cash funds) in.
  final String? baseCurrency;

  factory RegionConfig.fromJson(Map<String, dynamic> json) {
    final region = RegionConfig(
      id: (json['id'] as num).toInt(),
      regionCode: json['region_code'] as String? ?? '',
      regionName: json['region_name'] as String? ?? '',
      companyName: json['company_name'] as String?,
      logoUrl: json['logo_url'] as String?,
      baseCurrency: json['base_currency'] as String?,
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
    double? uncommitted,
  }) : _uncommitted = uncommitted;

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
  });

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

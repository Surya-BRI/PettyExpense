import 'enums.dart';

class AuthUser {
  const AuthUser({
    required this.id,
    required this.displayName,
    required this.role,
    this.username,
    this.email,
    this.departmentId,
  });

  final int id;
  final String displayName;
  final String role;
  final String? username;
  final String? email;
  final int? departmentId;

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
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'display_name': displayName,
        'role': role,
        'username': username,
        'email': email,
        'department_id': departmentId,
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
      duplicateWarning: json['duplicate_warning'] == null
          ? null
          : DuplicateWarning.fromJson(json['duplicate_warning'] as Map<String, dynamic>),
      ocrStatus: json['ocr_status'] as String?,
      reconciliationMismatch: json['reconciliation_mismatch'] == true,
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

  factory ReceiptInfo.fromJson(Map<String, dynamic> json) {
    return ReceiptInfo(
      id: (json['id'] as num).toInt(),
      s3Key: json['s3_key'] as String,
      contentType: json['content_type'] as String?,
      ocrVendor: json['ocr_vendor'] as String?,
      ocrAmount: (json['ocr_amount'] as num?)?.toDouble(),
      ocrDate: json['ocr_date'] as String?,
      ocrConfidence: (json['ocr_confidence'] as num?)?.toDouble(),
      imageHash: json['image_hash'] as String?,
      imageUrl: json['image_url'] as String?,
    );
  }
}

class ClaimHistoryItem {
  const ClaimHistoryItem({
    required this.id,
    required this.actorId,
    required this.action,
    this.stage,
    this.remarks,
    this.createdAt,
  });

  final int id;
  final int actorId;
  final String action; // approve | dispute | reject | submitted | edited | paid
  final String? stage; // hod | department_hod | accountant | finance_manager | employee
  final String? remarks;
  final String? createdAt;

  factory ClaimHistoryItem.fromJson(Map<String, dynamic> json) {
    return ClaimHistoryItem(
      id: (json['id'] as num).toInt(),
      actorId: (json['actor_id'] as num).toInt(),
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
    this.remarks,
    this.currentStage,
    this.disputeReturned = false,
    this.createdAt,
    this.updatedAt,
    this.submittedAt,
    this.decidedAt,
    this.paidAt,
    this.receipt,
    this.history,
    this.duplicateWarning,
    this.stageSequence = const [],
  });

  final int id;
  final int employeeId;
  final String type;
  final String? regionCode;
  final String? employeeName;
  final String? vendorName;
  final double amount;
  final String currency;
  final double vatAmount;
  final double? totalAmount;
  final String? billDate;
  final int categoryId;
  final String? categoryName;
  final int? projectId;
  final String? opNumber;
  final String status;
  final String? currentStage;
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
  final List<String> stageSequence;

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
      vatAmount: (json['vat_amount'] as num?)?.toDouble() ?? 0,
      totalAmount: (json['total_amount'] as num?)?.toDouble(),
      billDate: json['bill_date'] as String?,
      categoryId: (json['category_id'] as num?)?.toInt() ?? 0,
      categoryName: json['category_name'] as String?,
      projectId: (json['project_id'] as num?)?.toInt(),
      opNumber: json['op_number'] as String?,
      status: json['status'] as String? ?? 'draft',
      currentStage: json['current_stage'] as String?,
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
      stageSequence: (json['stage_sequence'] as List?)?.map((e) => e as String).toList() ?? const [],
    );
  }
}

class CategoryRef {
  const CategoryRef({required this.id, required this.name, this.nameAr});

  final int id;
  final String name;
  final String? nameAr;

  factory CategoryRef.fromJson(Map<String, dynamic> json) {
    return CategoryRef(
      id: (json['id'] as num).toInt(),
      name: json['name'] as String,
      nameAr: json['name_ar'] as String?,
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

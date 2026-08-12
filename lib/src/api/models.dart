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
    required this.amount,
    required this.date,
    this.confidence,
    this.rawText,
    this.imageUrl,
    this.imageHash,
    this.duplicateWarning,
  });

  final int receiptId;
  final String s3Key;
  final String vendor;
  final double amount;
  final String date;
  final double? confidence;
  final String? rawText;
  final String? imageUrl;
  final String? imageHash;
  final DuplicateWarning? duplicateWarning;

  factory OcrResult.fromJson(Map<String, dynamic> json) {
    return OcrResult(
      receiptId: (json['receipt_id'] as num).toInt(),
      s3Key: json['s3_key'] as String,
      vendor: (json['vendor'] ?? '') as String,
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      date: (json['date'] ?? '') as String,
      confidence: (json['confidence'] as num?)?.toDouble(),
      rawText: json['raw_text'] as String?,
      imageUrl: json['image_url'] as String?,
      imageHash: json['image_hash'] as String?,
      duplicateWarning: json['duplicate_warning'] == null
          ? null
          : DuplicateWarning.fromJson(json['duplicate_warning'] as Map<String, dynamic>),
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
  });

  final int id;
  final int employeeId;
  final String type;
  final String? regionCode;
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

  /// Backward-compat display helper — old UI code refers to "vendor".
  String get vendor => vendorName ?? '';

  /// Backward-compat display helper — old UI code refers to "category".
  String get category => categoryName ?? '';

  factory ExpenseClaim.fromJson(Map<String, dynamic> json) {
    return ExpenseClaim(
      id: (json['id'] as num).toInt(),
      employeeId: (json['employee_id'] as num?)?.toInt() ?? 0,
      type: json['type'] as String? ?? 'reimbursement',
      regionCode: json['region_code'] as String?,
      vendorName: json['vendor_name'] as String?,
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      currency: json['currency'] as String? ?? 'INR',
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

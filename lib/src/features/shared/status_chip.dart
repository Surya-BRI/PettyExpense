import 'package:flutter/material.dart';

import '../../api/models.dart';
import '../../theme/app_theme.dart';

class StatusChip extends StatelessWidget {
  const StatusChip({super.key, required this.status, this.paymentStatus, this.type});

  /// Splits "approved" into Approved – Unpaid (reimbursement waiting for payment) and
  /// Approved – Settled (petty cash, paid from the fund at approval).
  StatusChip.forClaim(ExpenseClaim claim, {Key? key})
      : this(key: key, status: claim.status, paymentStatus: claim.paymentStatus, type: claim.type);

  final String status;
  final String? paymentStatus;
  final String? type;

  bool get _awaitingPayment => status == 'approved' && paymentStatus == 'unpaid';
  bool get _settled => status == 'approved' && type == 'petty_cash';

  Color get _color {
    if (_awaitingPayment) return AppColors.orange;
    switch (status) {
      case 'draft':
        return AppColors.textSecondary;
      case 'submitted':
        return AppColors.orange;
      case 'pending_review':
        return AppColors.darkBlue;
      case 'in_progress':
        return AppColors.textSecondary;
      case 'approved':
        return AppColors.success;
      case 'rejected':
        return AppColors.danger;
      case 'disputed':
        return AppColors.orange;
      case 'paid':
        return AppColors.darkBlue;
      default:
        return AppColors.textSecondary;
    }
  }

  String get _label {
    if (_awaitingPayment) return 'APPROVED – UNPAID';
    if (_settled) return 'APPROVED – SETTLED';
    if (status == 'pending_review') return 'Review needed';
    if (status == 'in_progress') return 'In progress';
    return status.toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: _color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        _label,
        style: TextStyle(
          color: _color,
          fontWeight: FontWeight.w700,
          fontSize: 11,
          letterSpacing: 0.4,
        ),
      ),
    );
  }
}

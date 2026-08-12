import 'package:flutter/material.dart';

import '../../theme/app_theme.dart';

class StatusChip extends StatelessWidget {
  const StatusChip({super.key, required this.status});

  final String status;

  Color get _color {
    switch (status) {
      case 'draft':
        return AppColors.textSecondary;
      case 'submitted':
        return AppColors.orange;
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

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: _color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        status.toUpperCase(),
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

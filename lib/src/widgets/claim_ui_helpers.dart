import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

/// Small pill showing the claim type ("Reimbursement" / "Petty cash") —
/// shared between the employee claim-detail and approver review screens.
class ClaimTypeTag extends StatelessWidget {
  const ClaimTypeTag({super.key, required this.type});

  final String type;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.lightBlue,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        type == 'petty_cash' ? 'Petty cash' : 'Reimbursement',
        style: const TextStyle(
          color: AppColors.darkBlue,
          fontWeight: FontWeight.w600,
          fontSize: 11,
        ),
      ),
    );
  }
}

/// Label/value row for a details card (e.g. Category, Bill date, Project).
/// "None" values render muted, consistent across screens.
class KeyValueRow extends StatelessWidget {
  const KeyValueRow(this.label, this.value, {super.key, this.isLast = false, this.labelWidth = 110});

  final String label;
  final String value;
  final bool isLast;
  final double labelWidth;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: isLast ? 0 : 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: labelWidth, child: Text(label, style: const TextStyle(fontWeight: FontWeight.w600))),
          Expanded(
            child: Text(
              value,
              style: value == 'None' ? const TextStyle(color: AppColors.textSecondary) : null,
            ),
          ),
        ],
      ),
    );
  }
}

/// Label/value row for the Amount/VAT/Total breakdown at the top of a claim
/// card — `emphasize` bolds and enlarges the Total row.
class MoneyBreakdownRow extends StatelessWidget {
  const MoneyBreakdownRow(this.label, this.value, {super.key, this.emphasize = false});

  final String label;
  final String value;
  final bool emphasize;

  @override
  Widget build(BuildContext context) {
    final style = emphasize
        ? const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)
        : const TextStyle(color: AppColors.textSecondary);
    return Row(
      children: [
        Expanded(child: Text(label, style: style)),
        Text(value, style: style),
      ],
    );
  }
}

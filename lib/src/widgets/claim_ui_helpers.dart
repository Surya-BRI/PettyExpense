import 'package:flutter/material.dart';

import '../api/models.dart';
import '../theme/app_theme.dart';
import '../utils/dubai_time.dart';
import 'app_card.dart';

/// A bordered table card for claim details — shared between employee and
/// approver detail screens. Wrap rows in [ClaimDetailRow].
class ClaimDetailsCard extends StatelessWidget {
  const ClaimDetailsCard({super.key, required this.title, required this.rows});

  final String title;
  final List<ClaimDetailRow> rows;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.divider),
        borderRadius: BorderRadius.circular(12),
        color: AppColors.card,
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.divider)),
            ),
            child: Text(
              title,
              style: TextStyle(fontSize: 12.5, color: AppColors.textSecondary, fontWeight: FontWeight.w500),
            ),
          ),
          ...rows.indexed.map((e) => ClaimDetailRow(
                label: e.$2.label,
                value: e.$2.value,
                isLast: e.$1 == rows.length - 1,
              )),
        ],
      ),
    );
  }
}

/// One row inside a [ClaimDetailsCard].
class ClaimDetailRow extends StatelessWidget {
  const ClaimDetailRow({super.key, required this.label, required this.value, this.isLast = false});

  final String label;
  final String value;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        border: Border(
          bottom: isLast ? BorderSide.none : const BorderSide(color: AppColors.divider),
        ),
      ),
      child: IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              width: 120,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: const BoxDecoration(
                color: AppColors.background,
                border: Border(right: BorderSide(color: AppColors.divider)),
              ),
              child: Text(
                label,
                style: const TextStyle(fontSize: 12.5, color: AppColors.textSecondary, fontWeight: FontWeight.w500),
              ),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                child: Text(
                  value,
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

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

/// Styled history timeline shared between the employee claim-detail and approver
/// review screens. Shows newest entry first with avatar, name, action chip and
/// timestamp.
class ClaimHistoryList extends StatelessWidget {
  const ClaimHistoryList({super.key, required this.history, this.hideInternal = false});

  final List<ClaimHistoryItem> history;
  // When true, filters out employee-internal actions (edited/created) that are
  // noise for approvers who only care about submission and approval steps.
  final bool hideInternal;

  static const _stageLabels = {
    'hod': 'HOD',
    'department_hod': 'Dept. HOD',
    'accountant': 'Accountant',
    'finance_manager': 'Finance Manager',
    'employee': 'Employee',
  };

  static const _actionColors = {
    'approve': Color(0xFF2E7D32),
    'approved': Color(0xFF2E7D32),
    'paid': Color(0xFF1565C0),
    'submitted': Color(0xFF1565C0),
    'created': Color(0xFF1565C0),
    'edited': Color(0xFF6D4C41),
    'dispute': Color(0xFFE65100),
    'disputed': Color(0xFFE65100),
    'reject': Color(0xFFC62828),
    'rejected': Color(0xFFC62828),
  };

  static const _actionLabels = {
    'approve': 'Approved',
    'approved': 'Approved',
    'paid': 'Marked paid',
    'submitted': 'Submitted',
    'created': 'Created',
    'edited': 'Edited',
    'dispute': 'Disputed',
    'disputed': 'Disputed',
    'reject': 'Rejected',
    'rejected': 'Rejected',
  };

  String _initials(String? name) {
    if (name == null || name.trim().isEmpty) return '?';
    final parts = name.trim().split(RegExp(r'\s+'));
    if (parts.length == 1) return parts[0][0].toUpperCase();
    return '${parts[0][0]}${parts.last[0]}'.toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    final visible = hideInternal
        ? history.where((h) => h.action != 'edited' && h.action != 'created').toList()
        : history;

    if (visible.isEmpty) {
      return AppCard(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: const Text('No activity yet', style: TextStyle(color: AppColors.textSecondary)),
      );
    }

    final items = visible.reversed.toList();
    return AppCard(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: Column(
        children: [
          for (final (i, h) in items.indexed) ...[
            if (i > 0) const Divider(height: 1, indent: 52),
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 10),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Avatar
                  CircleAvatar(
                    radius: 18,
                    backgroundColor: AppColors.lightBlue,
                    child: Text(
                      _initials(h.actorName),
                      style: const TextStyle(
                        color: AppColors.darkBlue,
                        fontWeight: FontWeight.w700,
                        fontSize: 12,
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            Expanded(
                              child: Text(
                                h.actorName ?? _stageLabels[h.stage] ?? h.stage ?? '—',
                                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13.5),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              formatDubaiTime(h.createdAt),
                              style: const TextStyle(color: AppColors.textSecondary, fontSize: 11),
                            ),
                          ],
                        ),
                        const SizedBox(height: 3),
                        Row(
                          children: [
                            _ActionChip(action: h.action),
                            if (h.stage != null) ...[
                              const SizedBox(width: 6),
                              Text(
                                _stageLabels[h.stage] ?? h.stage!,
                                style: const TextStyle(color: AppColors.textSecondary, fontSize: 11.5),
                              ),
                            ],
                          ],
                        ),
                        if (h.remarks != null && h.remarks!.isNotEmpty) ...[
                          const SizedBox(height: 4),
                          Text(
                            h.remarks!,
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: AppColors.textSecondary,
                                  fontStyle: FontStyle.italic,
                                ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _ActionChip extends StatelessWidget {
  const _ActionChip({required this.action});
  final String action;

  static const _colors = ClaimHistoryList._actionColors;
  static const _labels = ClaimHistoryList._actionLabels;

  @override
  Widget build(BuildContext context) {
    final color = _colors[action] ?? AppColors.textSecondary;
    final label = _labels[action] ?? action;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.10),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        label,
        style: TextStyle(color: color, fontWeight: FontWeight.w600, fontSize: 11),
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

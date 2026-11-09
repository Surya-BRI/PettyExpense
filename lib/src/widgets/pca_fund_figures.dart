import 'package:flutter/material.dart';

import '../api/models.dart';
import '../theme/app_theme.dart';
import '../utils/money.dart';

/// Approved limit, spent, available, pending — the four PCA numbers from the BRI doc.
class PcaFundFigures extends StatelessWidget {
  const PcaFundFigures({super.key, required this.fund, this.compact = false});

  final PettyCashFund fund;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final gap = compact ? 6.0 : 8.0;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _HeroAvailable(fund: fund, compact: compact),
        SizedBox(height: gap),
        Row(
          children: [
            Expanded(
              child: _MetricTile(
                label: 'Approved limit',
                value: formatMoney(fund.currency, fund.approvedLimit),
                compact: compact,
              ),
            ),
            SizedBox(width: gap),
            Expanded(
              child: _MetricTile(
                label: 'Spent',
                value: formatMoney(fund.currency, fund.spent),
                compact: compact,
              ),
            ),
          ],
        ),
        SizedBox(height: gap),
        _MetricTile(
          label: 'Pending top-up',
          value: formatMoney(fund.currency, fund.pendingTopup),
          compact: compact,
          tint: fund.pendingTopup > 0 ? AppColors.warningSoft : AppColors.background,
        ),
      ],
    );
  }
}

class _HeroAvailable extends StatelessWidget {
  const _HeroAvailable({required this.fund, required this.compact});

  final PettyCashFund fund;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    // Employee advance with a hard limit (Professional Signs: 50%): lead with what can still
    // be used until the approved bills are paid (which refills it), not the whole balance.
    final limit = fund.spendLimit;
    final canUse = fund.uncommitted < 0 ? 0.0 : fund.uncommitted;
    final blocked = limit != null && canUse <= 0.004;
    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(horizontal: 14, vertical: compact ? 10 : 14),
      decoration: BoxDecoration(
        color: blocked ? AppColors.warningSoft : AppColors.lightBlue,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            limit != null ? 'Can use now' : 'Available',
            style: TextStyle(
              color: AppColors.darkBlue,
              fontWeight: FontWeight.w700,
              fontSize: compact ? 11 : 12,
              letterSpacing: 0.2,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            formatMoney(fund.currency, limit != null ? canUse : fund.available),
            style: TextStyle(
              color: AppColors.darkBlue,
              fontWeight: FontWeight.w800,
              fontSize: compact ? 20 : 24,
              height: 1.15,
            ),
          ),
          if (limit != null) ...[
            const SizedBox(height: 2),
            Text(
              blocked
                  ? 'Limit reached: you can use more once Accounts pays your approved bills.'
                  : 'Up to ${formatMoney(fund.currency, limit)} of bills until they are paid',
              style: TextStyle(
                fontSize: compact ? 11.5 : 12,
                color: blocked ? AppColors.orange : AppColors.textSecondary,
                fontWeight: blocked ? FontWeight.w700 : FontWeight.w400,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _MetricTile extends StatelessWidget {
  const _MetricTile({
    required this.label,
    required this.value,
    required this.compact,
    this.tint,
  });

  final String label;
  final String value;
  final bool compact;
  final Color? tint;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 12, vertical: compact ? 8 : 10),
      decoration: BoxDecoration(
        color: tint ?? AppColors.background,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: compact ? 11 : 12,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: compact ? 13 : 14,
              height: 1.25,
            ),
          ),
        ],
      ),
    );
  }
}

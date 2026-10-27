import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../theme/app_theme.dart';
import '../../utils/money.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/shimmer_box.dart';

final approverHistoryProvider = FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) {
  return ref.watch(apiClientProvider).approvalsHistory();
});

String _formatDate(String? raw) {
  if (raw == null) return '';
  final dt = DateTime.tryParse(raw);
  if (dt == null) return '';
  return DateFormat('MMM d, yyyy · h:mm a').format(dt.toLocal());
}

class ApproverHistoryScreen extends ConsumerWidget {
  const ApproverHistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(approverHistoryProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: BrandAppBar(title: 'My Actions', showNotificationAction: false),
      body: async.when(
        loading: () => const _HistorySkeleton(),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text('$e', textAlign: TextAlign.center),
          ),
        ),
        data: (items) {
          if (items.isEmpty) {
            return RefreshIndicator(
              onRefresh: () async => ref.invalidate(approverHistoryProvider),
              child: ListView(
                padding: const EdgeInsets.all(32),
                children: [
                  Padding(
                    padding: const EdgeInsets.only(top: 80),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 72,
                          height: 72,
                          decoration: const BoxDecoration(
                            color: AppColors.lightBlue,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            PhosphorIcons.clockClockwise(),
                            size: 36,
                            color: AppColors.darkBlue,
                          ),
                        ),
                        const SizedBox(height: 16),
                        const Text(
                          'No actions yet',
                          style: TextStyle(
                            fontWeight: FontWeight.w700,
                            fontSize: 16,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Claims you approve, dispute, or reject will appear here.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: AppColors.textSecondary),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(approverHistoryProvider),
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, i) {
                final item = items[i];
                final action = item['my_action'] as String? ?? '';
                final actionedAt = item['my_actioned_at'] as String?;
                final vendor = item['vendor_name'] as String? ?? '—';
                final currency = item['currency'] as String? ?? '';
                final amount = (item['amount'] as num?)?.toDouble() ?? 0;
                final employee = item['employee_name'] as String? ?? '';
                final category = item['category_name'] as String? ?? '';
                final status = item['status'] as String? ?? '';
                final stage = item['my_action_stage'] as String? ?? '';
                final regionCode = item['region_code'] as String?;
                final id = item['id'] as int?;

                return Material(
                  color: AppColors.card,
                  borderRadius: BorderRadius.circular(14),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(14),
                    onTap: id == null
                        ? null
                        : () => stage.isNotEmpty
                            ? context.push('/approvals/$stage/$id')
                            : context.push('/claim/$id'),
                    child: Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppColors.divider),
                      ),
                      padding: const EdgeInsets.all(14),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                width: 40,
                                height: 40,
                                decoration: BoxDecoration(
                                  color: _actionColor(action).withValues(alpha: 0.12),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Icon(
                                  _actionIcon(action),
                                  color: _actionColor(action),
                                  size: 20,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      vendor,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                        color: AppColors.textPrimary,
                                      ),
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      '${formatMoney(currency, amount)} · $category · $employee${regionCode != null ? ' · $regionCode' : ''}',
                                      style: const TextStyle(
                                        color: AppColors.textSecondary,
                                        fontSize: 13,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              ],
                          ),
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              _ActionBadge(action: action, stage: stage),
                              const Spacer(),
                              Text(
                                _formatDate(actionedAt),
                                style: const TextStyle(
                                  color: AppColors.textSecondary,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }

  Color _actionColor(String action) {
    switch (action) {
      case 'approve':
        return AppColors.success;
      case 'reject':
        return AppColors.danger;
      case 'dispute':
        return AppColors.orange;
      case 'vendor_resolved':
        return AppColors.darkBlue;
      default:
        return AppColors.textSecondary;
    }
  }

  IconData _actionIcon(String action) {
    switch (action) {
      case 'approve':
        return PhosphorIcons.checkCircle();
      case 'reject':
        return PhosphorIcons.xCircle();
      case 'dispute':
        return PhosphorIcons.arrowUUpLeft();
      case 'vendor_resolved':
        return PhosphorIcons.buildings();
      default:
        return PhosphorIcons.clock();
    }
  }
}

class _ActionBadge extends StatelessWidget {
  const _ActionBadge({required this.action, required this.stage});

  final String action;
  final String stage;

  @override
  Widget build(BuildContext context) {
    final label = switch (action) {
      'approve' => 'Approved',
      'reject' => 'Rejected',
      'dispute' => 'Disputed',
      'vendor_resolved' => 'Vendor linked',
      _ => action,
    };
    final stageLabel = switch (stage) {
      'hod' => 'HOD',
      'department_hod' => 'Dept HOD',
      'accountant' => 'Accountant',
      'finance_manager' => 'Finance Mgr',
      _ => stage,
    };

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: _color,
          ),
        ),
        if (stageLabel.isNotEmpty) ...[
          Text(
            ' · $stageLabel',
            style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
          ),
        ],
      ],
    );
  }

  Color get _color {
    switch (action) {
      case 'approve':
        return AppColors.success;
      case 'reject':
        return AppColors.danger;
      case 'dispute':
        return AppColors.orange;
      default:
        return AppColors.darkBlue;
    }
  }
}

class _HistorySkeleton extends StatelessWidget {
  const _HistorySkeleton();

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      physics: const NeverScrollableScrollPhysics(),
      itemCount: 6,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (_, __) => Container(
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.divider),
        ),
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const ShimmerBox(height: 40, width: 40, borderRadius: BorderRadius.all(Radius.circular(12))),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      ShimmerBox(height: 14, widthFraction: 0.5),
                      SizedBox(height: 6),
                      ShimmerBox(height: 12, widthFraction: 0.75),
                    ],
                  ),
                ),
                ShimmerBox(height: 28, width: 70, borderRadius: BorderRadius.circular(6)),
              ],
            ),
            const SizedBox(height: 10),
            const ShimmerBox(height: 12, widthFraction: 0.4),
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/money.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/claim_stage_tracker.dart';
import '../../widgets/shimmer_box.dart';
import '../shared/status_chip.dart';

final myClaimsProvider = FutureProvider.autoDispose<List<ExpenseClaim>>((ref) {
  return ref.watch(apiClientProvider).myClaims();
});

const _statusFilters = ['all', 'draft', 'submitted', 'disputed', 'approved', 'rejected', 'paid'];
const _statusFilterLabels = {
  'all': 'All',
  'draft': 'Draft',
  'submitted': 'Submitted',
  'disputed': 'Disputed',
  'approved': 'Approved',
  'rejected': 'Rejected',
  'paid': 'Paid',
};

class MyClaimsScreen extends ConsumerStatefulWidget {
  const MyClaimsScreen({super.key});

  @override
  ConsumerState<MyClaimsScreen> createState() => _MyClaimsScreenState();
}

class _MyClaimsScreenState extends ConsumerState<MyClaimsScreen> {
  String _statusFilter = 'all';

  Color _statusAccent(String status) {
    switch (status) {
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
        return AppColors.divider;
    }
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(myClaimsProvider);

    return Scaffold(
      appBar: BrandAppBar(
        title: 'My claims',
        actions: [
          PopupMenuButton<String>(
            initialValue: _statusFilter,
            onSelected: (s) => setState(() => _statusFilter = s),
            icon: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.filter_list),
                if (_statusFilter != 'all') ...[
                  const SizedBox(width: 4),
                  Text(
                    _statusFilterLabels[_statusFilter]!,
                    style: const TextStyle(fontSize: 13, color: Colors.white),
                  ),
                ],
              ],
            ),
            itemBuilder: (context) => _statusFilters
                .map((s) => PopupMenuItem(value: s, child: Text(_statusFilterLabels[s]!)))
                .toList(),
          ),
        ],
      ),
      body: async.when(
              loading: () => const _MyClaimsSkeleton(),
              error: (e, _) => Center(child: Text('$e')),
              data: (claims) {
                final filtered =
                    _statusFilter == 'all' ? claims : claims.where((c) => c.status == _statusFilter).toList();
                if (claims.isEmpty) {
                  return const Center(child: Text('No claims yet. Capture a receipt to start.'));
                }
                if (filtered.isEmpty) {
                  return Center(
                    child: Text('No ${_statusFilterLabels[_statusFilter]!.toLowerCase()} claims.'),
                  );
                }
                return ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
                  itemCount: filtered.length,
                  separatorBuilder: (context, index) => const SizedBox(height: 12),
                  itemBuilder: (context, i) {
                    final c = filtered[i];
                    final stageLabel = (c.status == 'submitted' || c.status == 'disputed')
                        ? ClaimStageTracker.compactLabel(c)
                        : null;
                    return Material(
                      color: AppColors.card,
                      elevation: 0,
                      borderRadius: BorderRadius.circular(12),
                      child: InkWell(
                        borderRadius: BorderRadius.circular(12),
                        onTap: () => context.push('/claim/${c.id}'),
                        child: Ink(
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppColors.divider),
                          ),
                          child: IntrinsicHeight(
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                Container(
                                  width: 3,
                                  decoration: BoxDecoration(
                                    color: _statusAccent(c.status),
                                    borderRadius: const BorderRadius.only(
                                      topLeft: Radius.circular(11),
                                      bottomLeft: Radius.circular(11),
                                    ),
                                  ),
                                ),
                                Expanded(
                                  child: Padding(
                                    padding: const EdgeInsets.fromLTRB(12, 12, 12, 8),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Expanded(
                                              child: Text(
                                                c.vendor,
                                                maxLines: 2,
                                                overflow: TextOverflow.ellipsis,
                                                style: const TextStyle(
                                                  fontWeight: FontWeight.w700,
                                                  fontSize: 15,
                                                  height: 1.25,
                                                  color: AppColors.textPrimary,
                                                ),
                                              ),
                                            ),
                                            const SizedBox(width: 8),
                                            StatusChip(status: c.status),
                                          ],
                                        ),
                                        const SizedBox(height: 8),
                                        Row(
                                          children: [
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                              decoration: BoxDecoration(
                                                color: AppColors.lightBlue,
                                                borderRadius: BorderRadius.circular(999),
                                              ),
                                              child: Text(
                                                c.category.isEmpty ? 'Other' : c.category,
                                                style: const TextStyle(
                                                  fontSize: 11,
                                                  fontWeight: FontWeight.w600,
                                                  color: AppColors.darkBlue,
                                                ),
                                              ),
                                            ),
                                            const SizedBox(width: 8),
                                            Text(
                                              formatMoney(c.currency, c.amount),
                                              style: const TextStyle(
                                                fontSize: 13,
                                                fontWeight: FontWeight.w600,
                                                color: AppColors.textPrimary,
                                              ),
                                            ),
                                            const Padding(
                                              padding: EdgeInsets.symmetric(horizontal: 6),
                                              child: Text(
                                                '·',
                                                style: TextStyle(
                                                  color: AppColors.textSecondary,
                                                  fontSize: 13,
                                                ),
                                              ),
                                            ),
                                            Text(
                                              c.billDate ?? '-',
                                              style: const TextStyle(
                                                fontSize: 12,
                                                color: AppColors.textSecondary,
                                              ),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: 8),
                                        Row(
                                          children: [
                                            if (stageLabel != null)
                                              Container(
                                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                                decoration: BoxDecoration(
                                                  color: AppColors.lightBlue,
                                                  borderRadius: BorderRadius.circular(999),
                                                  border: Border.all(color: AppColors.darkBlue.withValues(alpha: 0.3)),
                                                ),
                                                child: Row(
                                                  mainAxisSize: MainAxisSize.min,
                                                  children: [
                                                    const Icon(Icons.timeline, size: 14, color: AppColors.darkBlue),
                                                    const SizedBox(width: 4),
                                                    Text(
                                                      stageLabel,
                                                      style: const TextStyle(
                                                        fontSize: 12,
                                                        fontWeight: FontWeight.w700,
                                                        color: AppColors.darkBlue,
                                                      ),
                                                    ),
                                                  ],
                                                ),
                                              ),
                                            const Spacer(),
                                            TextButton(
                                              style: TextButton.styleFrom(
                                                foregroundColor: AppColors.brightBlue,
                                                padding: const EdgeInsets.symmetric(horizontal: 4),
                                                minimumSize: Size.zero,
                                                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                                visualDensity: VisualDensity.compact,
                                              ),
                                              onPressed: () => context.push('/claim/${c.id}'),
                                              child: const Text(
                                                'View claim',
                                                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    );
                  },
                );
              },
            ),
    );
  }
}

class _MyClaimsSkeleton extends StatelessWidget {
  const _MyClaimsSkeleton();

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
      physics: const NeverScrollableScrollPhysics(),
      itemCount: 6,
      separatorBuilder: (context, index) => const SizedBox(height: 12),
      itemBuilder: (context, i) {
        return Container(
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.divider),
          ),
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              Row(
                children: [
                  Expanded(child: ShimmerBox(height: 16, widthFraction: 0.5)),
                  SizedBox(width: 8),
                  ShimmerBox(height: 20, width: 70, borderRadius: BorderRadius.all(Radius.circular(999))),
                ],
              ),
              SizedBox(height: 10),
              ShimmerBox(height: 12, widthFraction: 0.7),
            ],
          ),
        );
      },
    );
  }
}

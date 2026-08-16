import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/money.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/shimmer_box.dart';
import '../shared/status_chip.dart';

final approvalsQueueProvider =
    FutureProvider.autoDispose.family<List<ExpenseClaim>, String>((ref, stage) {
  return ref.watch(apiClientProvider).approvalsQueue(stage);
});

const _stageLabels = {
  'hod': 'HOD queue',
  'department_hod': 'Department HOD queue',
  'accountant': 'Accountant queue',
  'finance_manager': 'Finance Manager queue',
};

// The backend only ever returns 'submitted' or 'disputed' claims for a queue
// (ACTIONABLE_STATUSES) — this filter just lets the approver split those two
// apart instead of scanning one mixed list.
const _statusFilters = ['all', 'submitted', 'disputed'];
const _statusFilterLabels = {
  'all': 'All',
  'submitted': 'New',
  'disputed': 'Disputed',
};

/// One screen, parameterized by stage — an HOD and an Accountant see the same
/// widget tree, just filtered to their own stage via the backend query.
class ApprovalQueueScreen extends ConsumerStatefulWidget {
  const ApprovalQueueScreen({super.key, required this.stage});

  final String stage;

  @override
  ConsumerState<ApprovalQueueScreen> createState() => _ApprovalQueueScreenState();
}

class _ApprovalQueueScreenState extends ConsumerState<ApprovalQueueScreen> {
  String _statusFilter = 'all';

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(approvalsQueueProvider(widget.stage));

    return Scaffold(
      appBar: BrandAppBar(title: _stageLabels[widget.stage] ?? 'Approvals'),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: Row(
              children: _statusFilters
                  .map(
                    (s) => Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(_statusFilterLabels[s]!),
                        selected: _statusFilter == s,
                        onSelected: (_) => setState(() => _statusFilter = s),
                      ),
                    ),
                  )
                  .toList(),
            ),
          ),
          Expanded(
            child: async.when(
              loading: () => const _QueueSkeleton(),
              error: (e, _) => Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text('$e', textAlign: TextAlign.center),
                ),
              ),
              data: (claims) {
                final filtered = _statusFilter == 'all'
                    ? claims
                    : claims.where((c) => c.status == _statusFilter).toList();
                if (filtered.isEmpty) {
                  return Center(
                    child: Text(
                      claims.isEmpty
                          ? 'Nothing waiting for your approval.'
                          : 'No ${_statusFilterLabels[_statusFilter]!.toLowerCase()} claims right now.',
                    ),
                  );
                }
                return ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: filtered.length,
                  separatorBuilder: (context, index) => const SizedBox(height: 10),
                  itemBuilder: (context, i) {
                    final c = filtered[i];
                    return Material(
                      color: AppColors.card,
                      borderRadius: BorderRadius.circular(14),
                      child: InkWell(
                        borderRadius: BorderRadius.circular(14),
                        onTap: () => context.push('/approvals/${widget.stage}/${c.id}'),
                        child: Container(
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(color: AppColors.divider),
                          ),
                          padding: const EdgeInsets.all(14),
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      c.vendor,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                        color: AppColors.textPrimary,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      '${formatMoney(c.currency, c.amount)} · ${c.category} · employee #${c.employeeId}',
                                      style: const TextStyle(color: AppColors.textSecondary),
                                    ),
                                  ],
                                ),
                              ),
                              StatusChip(status: c.status),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _QueueSkeleton extends StatelessWidget {
  const _QueueSkeleton();

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      physics: const NeverScrollableScrollPhysics(),
      itemCount: 6,
      separatorBuilder: (context, index) => const SizedBox(height: 10),
      itemBuilder: (context, i) {
        return Container(
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.divider),
          ),
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    ShimmerBox(height: 15, widthFraction: 0.5),
                    SizedBox(height: 8),
                    ShimmerBox(height: 13, widthFraction: 0.8),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              ShimmerBox(height: 20, width: 70, borderRadius: BorderRadius.circular(999)),
            ],
          ),
        );
      },
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:intl/intl.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../widgets/app_nav_drawer.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/shimmer_box.dart';

// 'submitted' (New) first, 'disputed' second, 'approved' (awaiting payment) last.
const _statusSortPriority = {'submitted': 0, 'disputed': 1, 'approved': 2};

DateTime? _parseDate(String? raw) => raw == null ? null : DateTime.tryParse(raw);

List<ExpenseClaim> _sortedForQueue(List<ExpenseClaim> claims) {
  final sorted = List<ExpenseClaim>.from(claims);
  sorted.sort((a, b) {
    final priority = (_statusSortPriority[a.status] ?? 99).compareTo(_statusSortPriority[b.status] ?? 99);
    if (priority != 0) return priority;
    final aDate = _parseDate(a.submittedAt) ?? _parseDate(a.createdAt);
    final bDate = _parseDate(b.submittedAt) ?? _parseDate(b.createdAt);
    if (aDate == null || bDate == null) return 0;
    return bDate.compareTo(aDate); // newest first
  });
  return sorted;
}

String _formatDate(String? raw) {
  final date = _parseDate(raw);
  if (date == null) return '';
  return DateFormat('MMM d, yyyy').format(date.toLocal());
}

String _formatAmount(double amount) =>
    NumberFormat('#,##0.00').format(amount);

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

// Status filters for the queue. Finance Manager also sees 'approved' (pending payment).
const _statusFilters = ['all', 'submitted', 'disputed', 'approved'];
const _statusFilterLabels = {
  'all': 'All',
  'submitted': 'New',
  'disputed': 'Disputed',
  'approved': 'Pending payment',
};

/// One screen, parameterized by stage — an HOD and an Accountant see the same
/// widget tree, just filtered to their own stage via the backend query.
class ApprovalQueueScreen extends ConsumerStatefulWidget {
  const ApprovalQueueScreen({super.key, required this.stage, this.initialFilter});

  final String stage;
  final String? initialFilter;

  @override
  ConsumerState<ApprovalQueueScreen> createState() => _ApprovalQueueScreenState();
}

class _ApprovalQueueScreenState extends ConsumerState<ApprovalQueueScreen> {
  late String _statusFilter;

  @override
  void initState() {
    super.initState();
    _statusFilter = widget.initialFilter ?? 'all';
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(approvalsQueueProvider(widget.stage));

    return Scaffold(
      drawer: const AppNavDrawer(),
      appBar: BrandAppBar(title: _stageLabels[widget.stage] ?? 'Approvals', showNotificationAction: false),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _statusFilters
                    .where((s) => s != 'approved' || widget.stage == 'finance_manager')
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
                final filtered = _sortedForQueue(
                  _statusFilter == 'all' ? claims : claims.where((c) => c.status == _statusFilter).toList(),
                );
                if (filtered.isEmpty) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Text(
                        claims.isEmpty
                            ? 'Nothing waiting for your action.'
                            : 'No ${_statusFilterLabels[_statusFilter]!.toLowerCase()} claims right now.',
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: AppColors.textSecondary),
                      ),
                    ),
                  );
                }
                return ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: filtered.length,
                  separatorBuilder: (context, index) => const SizedBox(height: 10),
                  itemBuilder: (context, i) {
                    final c = filtered[i];
                    final isPendingPayment = c.status == 'approved';
                    final accentColor = isPendingPayment ? AppColors.success : AppColors.darkBlue;
                    final buttonLabel = isPendingPayment ? 'Mark paid' : 'View claim';
                    return Material(
                      color: AppColors.card,
                      borderRadius: BorderRadius.zero,
                      child: InkWell(
                        borderRadius: BorderRadius.zero,
                        onTap: () => context.push('/approvals/${widget.stage}/${c.id}'),
                        child: Container(
                          decoration: BoxDecoration(
                            border: Border.all(color: AppColors.divider),
                          ),
                          child: ClipRect(
                            child: IntrinsicHeight(
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  // Left accent bar — green for awaiting payment, blue for review
                                  Container(
                                    width: 4,
                                    color: accentColor,
                                  ),
                                  Expanded(
                                    child: Padding(
                                      padding: const EdgeInsets.fromLTRB(12, 12, 12, 12),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          // Vendor name
                                          Text(
                                            c.vendor,
                                            style: const TextStyle(
                                              fontWeight: FontWeight.w700,
                                              fontSize: 14.5,
                                              color: AppColors.textPrimary,
                                            ),
                                          ),
                                          const SizedBox(height: 5),
                                          // Employee · category
                                          Text(
                                            '${c.employeeDisplay} · ${c.category}',
                                            style: const TextStyle(
                                              color: AppColors.textSecondary,
                                              fontSize: 12.5,
                                            ),
                                          ),
                                          const SizedBox(height: 10),
                                          // Amount
                                          Text(
                                            '${_formatAmount(c.amount)} ${c.currency}',
                                            style: const TextStyle(
                                              fontWeight: FontWeight.w700,
                                              fontSize: 15,
                                              color: AppColors.textPrimary,
                                            ),
                                          ),
                                          const SizedBox(height: 8),
                                          // Region tag + date + View claim button
                                          Row(
                                            children: [
                                              if (c.regionCode != null) ...[
                                                Container(
                                                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                                                  decoration: BoxDecoration(
                                                    color: AppColors.lightBlue,
                                                    borderRadius: BorderRadius.zero,
                                                  ),
                                                  child: Text(
                                                    c.regionCode!,
                                                    style: const TextStyle(
                                                      color: AppColors.darkBlue,
                                                      fontWeight: FontWeight.w600,
                                                      fontSize: 11,
                                                    ),
                                                  ),
                                                ),
                                                const SizedBox(width: 8),
                                              ],
                                              Text(
                                                _formatDate(c.submittedAt ?? c.createdAt),
                                                style: const TextStyle(
                                                  color: AppColors.textSecondary,
                                                  fontSize: 11.5,
                                                ),
                                              ),
                                              const Spacer(),
                                              FilledButton(
                                                onPressed: () => context.push('/approvals/${widget.stage}/${c.id}'),
                                                style: FilledButton.styleFrom(
                                                  backgroundColor: isPendingPayment ? AppColors.success : AppColors.orange,
                                                  shape: const RoundedRectangleBorder(),
                                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                                  minimumSize: Size.zero,
                                                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                                  textStyle: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600),
                                                ),
                                                child: Row(
                                                  mainAxisSize: MainAxisSize.min,
                                                  children: [
                                                    Text(buttonLabel),
                                                    const SizedBox(width: 4),
                                                    Icon(
                                                      isPendingPayment ? PhosphorIcons.checkCircle() : PhosphorIcons.arrowRight(),
                                                      size: 14,
                                                    ),
                                                  ],
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

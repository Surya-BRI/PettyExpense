import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_icons/phosphor_icons.dart';
import 'package:intl/intl.dart';

import '../../api/api_client.dart';
import '../../api/enums.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/currency.dart';
import '../../utils/money.dart';
import '../../widgets/app_nav_drawer.dart' show AppNavDrawer, companyLabel;
import '../../widgets/brand_app_bar.dart';
import '../../widgets/region_filter_dropdown.dart';
import '../../widgets/shimmer_box.dart';
import '../authentication/auth_controller.dart';

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

final approvalsQueueProvider =
    FutureProvider.autoDispose.family<List<ExpenseClaim>, String>((ref, stage) async {
  final api = ref.watch(apiClientProvider);
  if (stage != 'hod') return api.approvalsQueue(stage);
  // An HOD approves their own department's bills ('hod') and other departments' lines they
  // own, e.g. IT items on a Sales bill ('department_hod') — one queue for both.
  final results = await Future.wait([api.approvalsQueue('hod'), api.approvalsQueue('department_hod')]);
  final seen = <int>{};
  return [for (final c in [...results[0], ...results[1]]) if (seen.add(c.id)) c];
});

/// Detail route for a queued claim: cross-department steps open in the department_hod view.
String _detailStageFor(String queueStage, ExpenseClaim c) =>
    queueStage == 'hod' && c.currentStage == 'department_hod' ? 'department_hod' : queueStage;

const _stageLabels = {
  'hod': 'HOD queue',
  'department_hod': 'Department HOD queue',
  'accountant': 'Accountant queue',
  'head_accountant': 'Head of Accountant queue',
  'finance_manager': 'Finance Manager queue',
};

// Approved reimbursements waiting for payment live on the Payments screen (/payments).
const _statusFilters = ['all', 'submitted', 'disputed'];
const _statusFilterLabels = {
  'all': 'All',
  'submitted': 'New',
  'disputed': 'Disputed',
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
  String? _region; // null = all companies

  @override
  void initState() {
    super.initState();
    final initial = widget.initialFilter;
    _statusFilter = _statusFilters.contains(initial) ? initial! : 'all';
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(approvalsQueueProvider(widget.stage));
    final user = ref.watch(authControllerProvider).user;
    final regions = regionFilterOptions(
      user?.allowedRegions ?? const <String>[],
      (async.asData?.value ?? const <ExpenseClaim>[]).map((c) => c.regionCode),
      onlyAllowed: UserRoleX.fromJson(user?.role) != UserRole.admin,
    );

    return Scaffold(
      drawer: const AppNavDrawer(),
      appBar: BrandAppBar(
        // Professional Signs (KSA) calls the Finance Manager step "Accounts Manager".
        title: widget.stage == 'finance_manager' &&
                (ref.watch(authControllerProvider).user?.usesEmployeeAdvances ?? false)
            ? 'Accounts Manager queue'
            : _stageLabels[widget.stage] ?? 'Approvals',
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: Row(
              children: [
                Expanded(
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
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
                ),
                if (regions.length > 1)
                  RegionFilterDropdown(
                    options: regions,
                    selected: _region,
                    onChanged: (code) => setState(() => _region = code),
                  ),
              ],
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
                  claims
                      .where((c) => _statusFilter == 'all' || c.status == _statusFilter)
                      .where((c) => regionFilterMatches(_region, regions, c.regionCode))
                      .toList(),
                );
                if (filtered.isEmpty) {
                  final statusWord = _statusFilter == 'all' ? '' : '${_statusFilterLabels[_statusFilter]!.toLowerCase()} ';
                  final regionPart =
                      regions.contains(_region) ? ' for ${companyLabel(_region!)}' : '';
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Text(
                        claims.isEmpty
                            ? 'Nothing waiting for your action.'
                            : 'No ${statusWord}claims$regionPart right now.',
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
                    final isPendingPayment = c.status == 'approved' && c.type != 'petty_cash';
                    final accentColor = isPendingPayment ? AppColors.success : AppColors.darkBlue;
                    final buttonLabel = isPendingPayment ? 'Mark paid' : 'View claim';
                    return Material(
                      color: AppColors.card,
                      borderRadius: BorderRadius.zero,
                      child: InkWell(
                        borderRadius: BorderRadius.zero,
                        onTap: () => context.push('/approvals/${_detailStageFor(widget.stage, c)}/${c.id}'),
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
                                          if ((c.billNumber ?? '').trim().isNotEmpty) ...[
                                            Text(
                                              'Invoice ${c.billNumber!.trim()}',
                                              style: const TextStyle(
                                                fontSize: 12,
                                                fontWeight: FontWeight.w600,
                                                color: AppColors.darkBlue,
                                              ),
                                            ),
                                            const SizedBox(height: 4),
                                          ],
                                          // Employee · category
                                          Text(
                                            '${c.employeeDisplay} · ${c.category}',
                                            style: const TextStyle(
                                              color: AppColors.textSecondary,
                                              fontSize: 12.5,
                                            ),
                                          ),
                                          const SizedBox(height: 10),
                                          // Bill amount, plus region amount when the bill is foreign.
                                          Text(
                                            formatMoney(c.currency, c.amount),
                                            style: const TextStyle(
                                              fontWeight: FontWeight.w700,
                                              fontSize: 15,
                                              color: AppColors.textPrimary,
                                            ),
                                          ),
                                          if (needsRegionConversion(c.currency, c.regionCode) &&
                                              c.exchangeRate > 0) ...[
                                            const SizedBox(height: 2),
                                            Text(
                                              formatMoney(
                                                baseCurrencyForRegion(c.regionCode),
                                                toRegionAmount(c.amount, c.exchangeRate),
                                              ),
                                              style: const TextStyle(
                                                fontWeight: FontWeight.w600,
                                                fontSize: 13,
                                                color: AppColors.textSecondary,
                                              ),
                                            ),
                                          ],
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
                                                onPressed: () => context.push('/approvals/${_detailStageFor(widget.stage, c)}/${c.id}'),
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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/money.dart';
import '../../widgets/app_nav_drawer.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/claim_stage_tracker.dart';
import '../../widgets/shimmer_box.dart';
import '../shared/status_chip.dart';

const _pageSize = 6;

class MyClaimsState {
  const MyClaimsState({
    this.items = const [],
    this.status = 'all',
    this.page = 0,
    this.total = 0,
    this.isLoading = true,
    this.error,
  });

  final List<ExpenseClaim> items;
  final String status;
  final int page;
  final int total;
  final bool isLoading;
  final Object? error;

  bool get hasNext => (page + 1) * _pageSize < total;
  bool get hasPrevious => page > 0;

  MyClaimsState copyWith({
    List<ExpenseClaim>? items,
    String? status,
    int? page,
    int? total,
    bool? isLoading,
    Object? error,
    bool clearError = false,
  }) {
    return MyClaimsState(
      items: items ?? this.items,
      status: status ?? this.status,
      page: page ?? this.page,
      total: total ?? this.total,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

class MyClaimsController extends StateNotifier<MyClaimsState> {
  MyClaimsController(this._ref) : super(const MyClaimsState()) {
    _fetch();
  }

  final Ref _ref;

  Future<void> _fetch() async {
    try {
      final page = await _ref.read(apiClientProvider).myClaims(
            limit: _pageSize,
            offset: state.page * _pageSize,
            status: state.status,
          );
      state = state.copyWith(items: page.items, total: page.total, isLoading: false, clearError: true);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e);
    }
  }

  Future<void> refresh() async {
    state = state.copyWith(page: 0, isLoading: true, clearError: true);
    await _fetch();
  }

  Future<void> nextPage() async {
    if (state.isLoading || !state.hasNext) return;
    state = state.copyWith(page: state.page + 1, isLoading: true);
    await _fetch();
  }

  Future<void> previousPage() async {
    if (state.isLoading || !state.hasPrevious) return;
    state = state.copyWith(page: state.page - 1, isLoading: true);
    await _fetch();
  }

  void setStatus(String status) {
    if (status == state.status) return;
    state = MyClaimsState(status: status, isLoading: true);
    _fetch();
  }
}

final myClaimsControllerProvider =
    StateNotifierProvider.autoDispose<MyClaimsController, MyClaimsState>((ref) => MyClaimsController(ref));

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
    final state = ref.watch(myClaimsControllerProvider);

    return Scaffold(
      drawer: const AppNavDrawer(),
      appBar: const BrandAppBar(
        title: 'My claims',
        showNotificationAction: false,
      ),
      body: Column(
        children: [
          Expanded(
            child: state.isLoading
                ? const _MyClaimsSkeleton()
                : state.error != null
                    ? Center(child: Text('${state.error}'))
                    : state.items.isEmpty
                        ? Center(
                            child: Text(
                              state.status == 'all'
                                  ? 'No claims yet. Capture a receipt to start.'
                                  : 'No ${_statusFilterLabels[state.status]!.toLowerCase()} claims.',
                            ),
                          )
                        : RefreshIndicator(
                            onRefresh: () => ref.read(myClaimsControllerProvider.notifier).refresh(),
                            child: ListView.separated(
                              padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
                              itemCount: state.items.length,
                              separatorBuilder: (context, index) => const SizedBox(height: 12),
                              itemBuilder: (context, i) {
                                final c = state.items[i];
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
                                                borderRadius: BorderRadius.circular(6),
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
                                        const SizedBox(height: 10),
                                        const Divider(height: 1, color: AppColors.divider),
                                        const SizedBox(height: 10),
                                        Row(
                                          children: [
                                            if (stageLabel != null)
                                              Container(
                                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                                decoration: BoxDecoration(
                                                  color: AppColors.lightBlue,
                                                  borderRadius: BorderRadius.circular(6),
                                                  border: Border.all(color: AppColors.darkBlue.withValues(alpha: 0.3)),
                                                ),
                                                child: Row(
                                                  mainAxisSize: MainAxisSize.min,
                                                  children: [
                                                    Icon(PhosphorIcons.trendUp(), size: 14, color: AppColors.darkBlue),
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
                            ),
                          ),
          ),
          if (!state.isLoading && state.error == null && state.items.isNotEmpty)
            _ClaimsPager(state: state),
        ],
      ),
    );
  }
}

class _ClaimsPager extends ConsumerWidget {
  const _ClaimsPager({required this.state});

  final MyClaimsState state;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final start = state.total == 0 ? 0 : state.page * _pageSize + 1;
    final end = (state.page * _pageSize + state.items.length).clamp(0, state.total);
    final notifier = ref.read(myClaimsControllerProvider.notifier);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: AppColors.divider)),
      ),
      child: Row(
        children: [
          TextButton.icon(
            onPressed: state.hasPrevious ? notifier.previousPage : null,
            icon: Icon(PhosphorIcons.caretLeft()),
            label: const Text('Back'),
          ),
          const Spacer(),
          Text(
            '$start-$end of ${state.total}',
            style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
          ),
          const Spacer(),
          TextButton.icon(
            onPressed: state.hasNext ? notifier.nextPage : null,
            icon: Icon(PhosphorIcons.caretRight()),
            label: const Text('Next'),
          ),
        ],
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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/dubai_time.dart';
import '../../utils/money.dart';
import '../../widgets/app_card.dart';
import '../../widgets/authenticated_image.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/claim_stage_tracker.dart';
import '../../widgets/claim_ui_helpers.dart';
import '../../widgets/shimmer_box.dart';
import '../shared/status_chip.dart';

String _fmtDate(String? raw) {
  if (raw == null || raw.isEmpty) return 'None';
  DateTime? dt = DateTime.tryParse(raw);
  if (dt == null) {
    final p = raw.split('/');
    if (p.length == 3) dt = DateTime.tryParse('${p[2]}-${p[1]}-${p[0]}');
  }
  return dt != null ? DateFormat('MMM d, yyyy').format(dt) : raw;
}

String _fmtDateTime(String? raw) {
  if (raw == null) return 'None';
  final dt = DateTime.tryParse(raw)?.toLocal();
  return dt != null ? DateFormat('MMM d, yyyy · h:mm a').format(dt) : raw;
}

final claimDetailProvider = FutureProvider.autoDispose
    .family<ExpenseClaim, int>((ref, id) {
      return ref.watch(apiClientProvider).getClaim(id);
    });

class ClaimDetailScreen extends ConsumerStatefulWidget {
  const ClaimDetailScreen({super.key, required this.claimId});

  final int claimId;

  @override
  ConsumerState<ClaimDetailScreen> createState() => _ClaimDetailScreenState();
}

class _ClaimDetailScreenState extends ConsumerState<ClaimDetailScreen> {
  bool _busy = false;
  String? _error;

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(claimDetailProvider(widget.claimId));
    final api = ref.watch(apiClientProvider);

    return Scaffold(
      appBar: const BrandAppBar(
        title: 'Claim detail',
        automaticallyImplyLeading: true,
      ),
      body: async.when(
        loading: () => const _ClaimDetailSkeleton(),
        error: (e, _) => Center(child: Text('$e')),
        data: (claim) {
          final imagePath = claim.receipt?.imageUrl;
          final total = claim.totalAmount ?? (claim.amount + claim.vatAmount);
          return ListView(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 110),
            children: [
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            claim.vendor,
                            style: Theme.of(context).textTheme.headlineSmall
                                ?.copyWith(fontWeight: FontWeight.w700),
                          ),
                        ),
                        StatusChip(status: claim.status),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ClaimTypeTag(type: claim.type),
                    const SizedBox(height: 16),
                    MoneyBreakdownRow(
                      'Amount excl. VAT',
                      formatMoney(claim.currency, claim.amount),
                    ),
                    const SizedBox(height: 6),
                    MoneyBreakdownRow(
                      'VAT',
                      formatMoney(claim.currency, claim.vatAmount),
                    ),
                    const Divider(height: 20),
                    MoneyBreakdownRow(
                      'Total',
                      formatMoney(claim.currency, total),
                      emphasize: true,
                    ),
                  ],
                ),
              ),
              if (claim.stageSequence.isNotEmpty) ...[
                const SizedBox(height: 16),
                AppCard(child: ClaimStageTracker(claim: claim)),
              ],
              if (claim.isMultiItem) ...[
                const SizedBox(height: 16),
                ClaimLineItemsList(claim: claim),
              ],
              if (imagePath != null && imagePath.isNotEmpty) ...[
                const SizedBox(height: 16),
                AppCard(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Receipt',
                        style: Theme.of(context).textTheme.titleSmall,
                      ),
                      const SizedBox(height: 10),
                      AuthenticatedImage(
                        path: imagePath,
                        height: 220,
                        width: double.infinity,
                      ),
                    ],
                  ),
                ),
              ],
              if (claim.duplicateWarning != null) ...[
                const SizedBox(height: 12),
                Material(
                  color: AppColors.warningSoft,
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(claim.duplicateWarning!.message),
                  ),
                ),
              ],
              const SizedBox(height: 16),
              ClaimDetailsCard(
                title: 'Details',
                rows: [
                  ClaimDetailRow(label: 'Type', value: claim.type == 'petty_cash' ? 'Petty cash' : 'Reimbursement'),
                  ClaimDetailRow(label: 'Category', value: claim.category),
                  if (claim.regionCode != null) ClaimDetailRow(label: 'Region', value: claim.regionCode!),
                  ClaimDetailRow(label: 'Bill date', value: _fmtDate(claim.billDate)),
                  if (claim.submittedAt != null) ClaimDetailRow(label: 'Submitted', value: _fmtDateTime(claim.submittedAt)),
                  if (claim.opNumber != null) ClaimDetailRow(label: 'OP', value: claim.opNumber!),
                  if (claim.remarks != null) ClaimDetailRow(label: 'Remarks', value: claim.remarks!),
                ],
              ),
              if (claim.status == 'draft') ...[
                const SizedBox(height: 16),
                OutlinedButton(
                  onPressed: () => context.push('/claim/${claim.id}/edit'),
                  child: const Text('Edit draft'),
                ),
                const SizedBox(height: 10),
                FilledButton(
                  onPressed: _busy
                      ? null
                      : () async {
                          setState(() {
                            _busy = true;
                            _error = null;
                          });
                          try {
                            await api.submitClaim(claim.id);
                            ref.invalidate(claimDetailProvider(widget.claimId));
                          } catch (e) {
                            final msg = e.toString();
                            setState(() => _error =
                                msg.startsWith('Exception: ') ? msg.substring(11) : msg);
                          } finally {
                            if (mounted) setState(() => _busy = false);
                          }
                        },
                  child: const Text('Submit draft'),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 8),
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                ],
              ],
              if (claim.status == 'disputed') ...[
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: _busy
                      ? null
                      : () async {
                          setState(() => _busy = true);
                          try {
                            await api.resubmitClaim(claim.id);
                            ref.invalidate(claimDetailProvider(widget.claimId));
                          } finally {
                            if (mounted) setState(() => _busy = false);
                          }
                        },
                  child: const Text('Resubmit corrected claim'),
                ),
              ],
              const SizedBox(height: 20),
              Text('History', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ClaimHistoryList(history: claim.history ?? []),
            ],
          );
        },
      ),
    );
  }
}

/// Mirrors the loaded layout's shape (header card, image card, details card,
/// history) so the page doesn't visually jump once data arrives — a spinner
/// gives no sense of what's coming, this does.
class _ClaimDetailSkeleton extends StatelessWidget {
  const _ClaimDetailSkeleton();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 110),
      physics: const NeverScrollableScrollPhysics(),
      children: [
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Expanded(
                    child: ShimmerBox(height: 24, widthFraction: 0.55),
                  ),
                  const SizedBox(width: 12),
                  ShimmerBox(
                    height: 22,
                    width: 80,
                    borderRadius: BorderRadius.circular(999),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              ShimmerBox(
                height: 18,
                width: 100,
                borderRadius: BorderRadius.circular(999),
              ),
              const SizedBox(height: 20),
              const ShimmerBox(height: 14, widthFraction: 1),
              const SizedBox(height: 10),
              const ShimmerBox(height: 14, widthFraction: 1),
              const SizedBox(height: 16),
              const ShimmerBox(height: 18, widthFraction: 1),
            ],
          ),
        ),
        const SizedBox(height: 16),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              ShimmerBox(height: 14, widthFraction: 0.6),
              SizedBox(height: 16),
              ShimmerBox(height: 14, widthFraction: 0.6),
              SizedBox(height: 16),
              ShimmerBox(height: 14, widthFraction: 0.6),
            ],
          ),
        ),
        const SizedBox(height: 16),
        AppCard(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              ShimmerBox(height: 14, width: 70),
              SizedBox(height: 10),
              ShimmerBox(height: 200, widthFraction: 1),
            ],
          ),
        ),
        const SizedBox(height: 16),
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: List.generate(
              5,
              (i) => Padding(
                padding: EdgeInsets.only(bottom: i == 4 ? 0 : 10),
                child: const ShimmerBox(height: 14, widthFraction: 1),
              ),
            ),
          ),
        ),
        const SizedBox(height: 20),
        const ShimmerBox(height: 18, width: 90),
        const SizedBox(height: 8),
        AppCard(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
          child: const ShimmerBox(height: 40, widthFraction: 1),
        ),
      ],
    );
  }
}

/// The item lines of a "Multiple items" claim, with their categories and the total.
class ClaimLineItemsList extends StatelessWidget {
  const ClaimLineItemsList({super.key, required this.claim});

  final ExpenseClaim claim;

  String _qty(double q) =>
      q == q.roundToDouble() ? q.toStringAsFixed(0) : q.toString();

  @override
  Widget build(BuildContext context) {
    final lines = claim.lineItems;
    final total = lines.fold(0.0, (sum, l) => sum + l.amount);
    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.divider),
        borderRadius: BorderRadius.circular(12),
        color: AppColors.card,
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.divider)),
            ),
            child: Row(
              children: [
                Text('Items', style: Theme.of(context).textTheme.titleSmall?.copyWith(color: AppColors.textSecondary)),
                const Spacer(),
                Text(
                  '${lines.length} item${lines.length == 1 ? '' : 's'}',
                  style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                ),
              ],
            ),
          ),
          // Line rows
          for (final (i, l) in lines.indexed)
            Container(
              decoration: BoxDecoration(
                border: Border(
                  bottom: BorderSide(color: AppColors.divider),
                ),
              ),
              child: IntrinsicHeight(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Line number
                    Container(
                      width: 36,
                      alignment: Alignment.center,
                      decoration: const BoxDecoration(
                        color: AppColors.background,
                        border: Border(right: BorderSide(color: AppColors.divider)),
                      ),
                      child: Text(
                        '${i + 1}',
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, fontWeight: FontWeight.w600),
                      ),
                    ),
                    // Description + meta
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(l.description, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                            if ([
                              if (l.quantity != null) 'Qty ${_qty(l.quantity!)}',
                              if (l.categoryName != null) l.categoryName!,
                              if (l.vatPercent != null) 'VAT ${l.vatPercent!.toStringAsFixed(l.vatPercent! == l.vatPercent!.roundToDouble() ? 0 : 2)}%',
                            ].isNotEmpty)
                              Padding(
                                padding: const EdgeInsets.only(top: 3),
                                child: Text(
                                  [
                                    if (l.quantity != null) 'Qty ${_qty(l.quantity!)}',
                                    if (l.categoryName != null) l.categoryName!,
                                    if (l.vatPercent != null) 'VAT ${l.vatPercent!.toStringAsFixed(l.vatPercent! == l.vatPercent!.roundToDouble() ? 0 : 2)}%',
                                  ].join(' · '),
                                  style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                    // Amount
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      decoration: const BoxDecoration(
                        border: Border(left: BorderSide(color: AppColors.divider)),
                      ),
                      child: Text(
                        formatMoney(claim.currency, l.amount),
                        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          // Total row
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            child: Row(
              children: [
                const Expanded(
                  child: Text('Total', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                ),
                Text(
                  formatMoney(claim.currency, total),
                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/money.dart';
import '../../widgets/app_card.dart';
import '../../widgets/authenticated_image.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/claim_stage_tracker.dart';
import '../../widgets/claim_ui_helpers.dart';
import '../../widgets/shimmer_box.dart';
import '../shared/status_chip.dart';

final claimDetailProvider =
    FutureProvider.autoDispose.family<ExpenseClaim, int>((ref, id) {
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
                            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                  fontWeight: FontWeight.w700,
                                ),
                          ),
                        ),
                        StatusChip(status: claim.status),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ClaimTypeTag(type: claim.type),
                    const SizedBox(height: 16),
                    MoneyBreakdownRow('Amount excl. VAT', formatMoney(claim.currency, claim.amount)),
                    const SizedBox(height: 6),
                    MoneyBreakdownRow('VAT', formatMoney(claim.currency, claim.vatAmount)),
                    const Divider(height: 20),
                    MoneyBreakdownRow('Total', formatMoney(claim.currency, total), emphasize: true),
                  ],
                ),
              ),
              if (claim.stageSequence.isNotEmpty) ...[
                const SizedBox(height: 16),
                AppCard(child: ClaimStageTracker(claim: claim)),
              ],
              if (imagePath != null && imagePath.isNotEmpty) ...[
                const SizedBox(height: 16),
                AppCard(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Receipt', style: Theme.of(context).textTheme.titleSmall),
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
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    KeyValueRow('Type', claim.type == 'petty_cash' ? 'Petty cash' : 'Reimbursement'),
                    KeyValueRow('Category', claim.category),
                    KeyValueRow('Bill date', claim.billDate ?? 'None'),
                    KeyValueRow('Project', claim.projectId?.toString() ?? 'None'),
                    KeyValueRow('OP', claim.opNumber ?? 'None'),
                    KeyValueRow('Remarks', claim.remarks ?? 'None', isLast: true),
                  ],
                ),
              ),
              if (claim.status == 'draft') ...[
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: _busy
                      ? null
                      : () async {
                          setState(() => _busy = true);
                          await api.submitClaim(claim.id);
                          ref.invalidate(claimDetailProvider(widget.claimId));
                          if (mounted) setState(() => _busy = false);
                        },
                  child: const Text('Submit draft'),
                ),
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
              AppCard(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                child: (claim.history ?? []).isEmpty
                    ? const Padding(
                        padding: EdgeInsets.symmetric(vertical: 12, horizontal: 8),
                        child: Text('None', style: TextStyle(color: AppColors.textSecondary)),
                      )
                    : Column(
                        children: [
                          for (final h in claim.history!)
                            ListTile(
                              dense: true,
                              title: Text('${h.stage ?? 'None'} · ${h.action}'),
                              subtitle: h.remarks != null && h.remarks!.isNotEmpty ? Text(h.remarks!) : null,
                              trailing: Text(
                                h.createdAt != null && h.createdAt!.length >= 16
                                    ? h.createdAt!.substring(0, 16)
                                    : '',
                                style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                              ),
                            ),
                        ],
                      ),
              ),
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
                  const Expanded(child: ShimmerBox(height: 24, widthFraction: 0.55)),
                  const SizedBox(width: 12),
                  ShimmerBox(height: 22, width: 80, borderRadius: BorderRadius.circular(999)),
                ],
              ),
              const SizedBox(height: 10),
              ShimmerBox(height: 18, width: 100, borderRadius: BorderRadius.circular(999)),
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

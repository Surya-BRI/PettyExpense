import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../widgets/brand_app_bar.dart';
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
    final currency = NumberFormat.currency(locale: 'en_IN', symbol: '₹');

    return Scaffold(
      appBar: const BrandAppBar(
        title: 'Claim detail',
        automaticallyImplyLeading: true,
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (claim) {
          final imagePath = claim.receipt?.imageUrl;
          return ListView(
            padding: const EdgeInsets.all(20),
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
              Text(currency.format(claim.amount), style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 16),
              if (imagePath != null && imagePath.isNotEmpty)
                ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: Image.network(
                    api.imageUrl(imagePath),
                    headers: api.authHeaders(),
                    height: 220,
                    width: double.infinity,
                    fit: BoxFit.cover,
                    errorBuilder: (context, error, stackTrace) => const SizedBox(
                      height: 120,
                      child: Center(child: Text('Image unavailable')),
                    ),
                  ),
                ),
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
              if (claim.status == 'disputed') ...[
                const SizedBox(height: 12),
                Material(
                  color: AppColors.warningSoft,
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(
                      'Sent back for correction at the ${claim.currentStage ?? '-'} stage'
                      '${claim.remarks != null && claim.remarks!.isNotEmpty ? ': ${claim.remarks}' : ''}',
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 16),
              _kv('Category', claim.category),
              _kv('Bill date', claim.billDate ?? '-'),
              _kv('Project', claim.projectId?.toString() ?? '-'),
              _kv('OP', claim.opNumber ?? '-'),
              _kv('Remarks', claim.remarks ?? '-'),
              _kv('Current stage', claim.currentStage ?? '-'),
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
              ...(claim.history ?? []).map(
                (h) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text('${h.stage ?? '-'} · ${h.action}'),
                  subtitle: Text(h.remarks != null ? h.remarks! : ''),
                  trailing: Text(h.createdAt != null && h.createdAt!.length >= 16 ? h.createdAt!.substring(0, 16) : ''),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _kv(String k, String v) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 130, child: Text(k, style: const TextStyle(fontWeight: FontWeight.w600))),
          Expanded(child: Text(v)),
        ],
      ),
    );
  }
}

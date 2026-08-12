import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../widgets/brand_app_bar.dart';
import '../claims/claim_detail_screen.dart';
import '../shared/status_chip.dart';
import 'approval_queue_screen.dart';

final approvalDetailProvider =
    FutureProvider.autoDispose.family<ExpenseClaim, int>((ref, id) {
  return ref.watch(apiClientProvider).getApprovalTransaction(id);
});

/// Reused across every approval stage (hod / department_hod / accountant /
/// finance_manager) — the stage only changes which actions the backend allows,
/// not the screen structure. Mirrors the old finance_detail_screen's _act() pattern.
class ApprovalDetailScreen extends ConsumerStatefulWidget {
  const ApprovalDetailScreen({super.key, required this.stage, required this.transactionId});

  final String stage;
  final int transactionId;

  @override
  ConsumerState<ApprovalDetailScreen> createState() => _ApprovalDetailScreenState();
}

class _ApprovalDetailScreenState extends ConsumerState<ApprovalDetailScreen> {
  final _comment = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _comment.dispose();
    super.dispose();
  }

  Future<void> _act(Future<ExpenseClaim> Function() action) async {
    setState(() => _busy = true);
    try {
      await action();
      ref.invalidate(approvalDetailProvider(widget.transactionId));
      ref.invalidate(approvalsQueueProvider(widget.stage));
      ref.invalidate(claimDetailProvider(widget.transactionId));
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Updated')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(approvalDetailProvider(widget.transactionId));
    final api = ref.watch(apiClientProvider);
    final currency = NumberFormat.currency(locale: 'en_IN', symbol: '₹');

    return Scaffold(
      appBar: const BrandAppBar(title: 'Review claim', automaticallyImplyLeading: true),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (claim) {
          final imagePath = claim.receipt?.imageUrl;
          final awaitingThisStage =
              (claim.status == 'submitted' || claim.status == 'disputed') && claim.currentStage == widget.stage;
          final awaitingPayment = claim.status == 'approved';

          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      claim.vendor,
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
                    ),
                  ),
                  StatusChip(status: claim.status),
                ],
              ),
              Text(currency.format(claim.amount), style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 12),
              if (imagePath != null)
                ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: Image.network(
                    api.imageUrl(imagePath),
                    headers: api.authHeaders(),
                    height: 240,
                    width: double.infinity,
                    fit: BoxFit.cover,
                  ),
                ),
              const SizedBox(height: 16),
              Text('Employee: #${claim.employeeId}'),
              Text('Category: ${claim.category}'),
              Text('Bill date: ${claim.billDate ?? '-'}'),
              Text('Current stage: ${claim.currentStage ?? '-'}'),
              if (claim.duplicateWarning != null) ...[
                const SizedBox(height: 12),
                Material(
                  color: AppColors.warningSoft,
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text('Duplicate warning: ${claim.duplicateWarning!.message}'),
                  ),
                ),
              ],
              if (!awaitingThisStage && !awaitingPayment) ...[
                const SizedBox(height: 16),
                Material(
                  color: AppColors.warningSoft,
                  borderRadius: BorderRadius.circular(12),
                  child: const Padding(
                    padding: EdgeInsets.all(12),
                    child: Text('This claim is not currently awaiting your action.'),
                  ),
                ),
              ],
              const SizedBox(height: 16),
              if (awaitingThisStage) ...[
                TextField(
                  controller: _comment,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: 'Comment',
                    helperText: 'Required when disputing or rejecting a claim',
                  ),
                ),
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: _busy
                      ? null
                      : () => _act(() => api.approveTransaction(claim.id, comment: _comment.text.trim())),
                  child: const Text('Approve'),
                ),
                const SizedBox(height: 8),
                OutlinedButton(
                  onPressed: _busy ? null : () => _requireComment(() => api.disputeTransaction(claim.id, comment: _comment.text.trim())),
                  child: const Text('Dispute (send back to employee)'),
                ),
                const SizedBox(height: 8),
                OutlinedButton(
                  style: OutlinedButton.styleFrom(foregroundColor: AppColors.danger),
                  onPressed: _busy ? null : () => _requireComment(() => api.rejectTransaction(claim.id, comment: _comment.text.trim())),
                  child: const Text('Reject'),
                ),
              ],
              if (awaitingPayment) ...[
                FilledButton(
                  onPressed: _busy ? null : () => _act(() => api.markPaid(claim.id, remarks: _comment.text.trim())),
                  child: const Text('Mark paid'),
                ),
              ],
              const SizedBox(height: 20),
              Text('History', style: Theme.of(context).textTheme.titleMedium),
              ...(claim.history ?? []).map(
                (h) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text('${h.stage ?? '-'} · ${h.action}'),
                  subtitle: Text('actor #${h.actorId}${h.remarks != null ? ' · ${h.remarks}' : ''}'),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  void _requireComment(Future<ExpenseClaim> Function() action) {
    if (_comment.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('A comment is required for this action')),
      );
      return;
    }
    _act(action);
  }
}

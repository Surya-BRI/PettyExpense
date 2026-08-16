import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/money.dart';
import '../../widgets/app_card.dart';
import '../../widgets/authenticated_image.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/claim_ui_helpers.dart';
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

    return Scaffold(
      appBar: const BrandAppBar(title: 'Review claim', automaticallyImplyLeading: true),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (claim) {
          final imagePath = claim.receipt?.imageUrl;
          final total = claim.totalAmount ?? (claim.amount + claim.vatAmount);
          final awaitingThisStage =
              (claim.status == 'submitted' || claim.status == 'disputed') && claim.currentStage == widget.stage;
          final awaitingPayment = claim.status == 'approved';

          return ListView(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
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
                            style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
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
                        height: 240,
                        width: double.infinity,
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 16),
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    KeyValueRow('Employee', claim.employeeDisplay),
                    KeyValueRow('Category', claim.category),
                    KeyValueRow('Bill date', claim.billDate ?? 'None'),
                    KeyValueRow(
                      'Current stage',
                      _stageLabels[claim.currentStage] ?? claim.currentStage ?? 'None',
                      isLast: true,
                    ),
                  ],
                ),
              ),
              if (claim.duplicateWarning != null) ...[
                const SizedBox(height: 16),
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
                  onChanged: (_) => setState(() {}),
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
                  onPressed: _busy || _comment.text.trim().isEmpty
                      ? null
                      : () => _requireComment(() => api.disputeTransaction(claim.id, comment: _comment.text.trim())),
                  child: const Text('Dispute (send back to employee)'),
                ),
                const SizedBox(height: 8),
                OutlinedButton(
                  style: OutlinedButton.styleFrom(foregroundColor: AppColors.danger),
                  onPressed: _busy || _comment.text.trim().isEmpty
                      ? null
                      : () => _requireComment(() => api.rejectTransaction(claim.id, comment: _comment.text.trim())),
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
                              contentPadding: EdgeInsets.zero,
                              title: Text('${_stageLabels[h.stage] ?? h.stage ?? 'None'} · ${h.action}'),
                              subtitle: Text(h.remarks != null && h.remarks!.isNotEmpty ? h.remarks! : ''),
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

const _stageLabels = {
  'hod': 'HOD',
  'department_hod': 'Department HOD',
  'accountant': 'Accountant',
  'finance_manager': 'Finance Manager',
};

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import 'package:intl/intl.dart';

import '../../utils/money.dart';
import '../../widgets/app_card.dart';
import '../../widgets/authenticated_image.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/claim_ui_helpers.dart';
import '../claims/claim_detail_screen.dart' show ClaimLineItemsList, claimDetailProvider;
import '../shared/status_chip.dart';
import 'approval_queue_screen.dart';
import 'approver_history_screen.dart' show approverHistoryProvider;

String _formatSubmittedAt(String? raw) {
  if (raw == null) return 'None';
  final dt = DateTime.tryParse(raw)?.toLocal();
  return dt != null ? DateFormat('MMM d, yyyy · h:mm a').format(dt) : raw;
}

String _formatBillDate(String? raw) {
  if (raw == null || raw.isEmpty) return 'None';
  // Try ISO (yyyy-MM-dd) first, then dd/MM/yyyy
  DateTime? dt = DateTime.tryParse(raw);
  if (dt == null) {
    final parts = raw.split('/');
    if (parts.length == 3) {
      dt = DateTime.tryParse('${parts[2]}-${parts[1]}-${parts[0]}');
    }
  }
  return dt != null ? DateFormat('MMM d, yyyy').format(dt) : raw;
}

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
    _commentFocus.dispose();
    super.dispose();
  }

  Future<void> _act(Future<ExpenseClaim> Function() action) async {
    setState(() => _busy = true);
    try {
      await action();
      ref.invalidate(approvalDetailProvider(widget.transactionId));
      ref.invalidate(approvalsQueueProvider(widget.stage));
      ref.invalidate(claimDetailProvider(widget.transactionId));
      ref.invalidate(approverHistoryProvider);
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
              ClaimDetailsCard(
                title: 'Details',
                rows: [
                  ClaimDetailRow(label: 'Employee', value: claim.employeeDisplay),
                  ClaimDetailRow(label: 'Category', value: claim.category),
                  if (claim.regionCode != null) ClaimDetailRow(label: 'Region', value: claim.regionCode!),
                  ClaimDetailRow(label: 'Bill date', value: _formatBillDate(claim.billDate)),
                  if (claim.submittedAt != null) ClaimDetailRow(label: 'Submitted', value: _formatSubmittedAt(claim.submittedAt)),
                  ClaimDetailRow(
                    label: 'Current stage',
                    value: _stageLabels[claim.currentStage] ?? claim.currentStage ?? 'None',
                  ),
                ],
              ),
              // Visible at every stage (employee-scoped -- see transaction_service._find_duplicate --
              // so it only ever fires against the SAME employee's own past claims, never a coincidence
              // across two different people). Purely informational outside Accountant, though: the
              // backend only blocks bulk-approve on it at the accountant stage -- HOD/Finance Manager
              // aren't required to act on it, just aware of it.
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
              if (claim.vendorUnmatched && widget.stage == 'accountant') ...[
                const SizedBox(height: 16),
                if (awaitingThisStage)
                  _VendorResolveCard(
                    transactionId: widget.transactionId,
                    rawVendorText: claim.vendorName ?? '',
                    busy: _busy,
                    onResolve: (vendorId, createNew) => _act(
                      () => api.resolveVendor(widget.transactionId, vendorId: vendorId, createNew: createNew),
                    ),
                  )
                else
                  Material(
                    color: AppColors.warningSoft,
                    borderRadius: BorderRadius.circular(12),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Text(
                        'Unmatched vendor: "${claim.vendorName}" is not in the vendor list yet — '
                        'the Accountant will confirm or link it.',
                      ),
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
                  focusNode: _commentFocus,
                  maxLines: 2,
                  onChanged: (_) => setState(() {}),
                  decoration: InputDecoration(
                    labelText: 'Comment',
                    hintText: 'Add a note…',
                    helperText: widget.stage == 'accountant' && claim.duplicateWarning != null
                        ? '* Required to approve, dispute or reject a duplicate-flagged claim'
                        : '* Required to dispute or reject',
                    helperStyle: const TextStyle(fontSize: 11.5, color: AppColors.textSecondary),
                  ),
                ),
                const SizedBox(height: 16),
                // "Warn, allow-with-justification" for a duplicate-flagged claim, but only where
                // that judgment call actually belongs -- Accountant stage (backend enforces this
                // too, see approval_service.advance). HOD/Finance Manager approve unblocked.
                Builder(builder: (context) {
                  final requiresJustification = widget.stage == 'accountant' && claim.duplicateWarning != null;
                  final blocked = _busy || (requiresJustification && _comment.text.trim().isEmpty);
                  return FilledButton.icon(
                    onPressed: blocked
                        ? null
                        : () => _act(() => api.approveTransaction(claim.id, comment: _comment.text.trim())),
                    style: FilledButton.styleFrom(
                      backgroundColor: AppColors.darkBlue,
                      foregroundColor: Colors.white,
                      textStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                      minimumSize: const Size.fromHeight(48),
                    ),
                    icon: Icon(PhosphorIcons.checkCircle(), size: 20),
                    label: Text(requiresJustification ? 'Approve (justify duplicate above)' : 'Approve'),
                  );
                }),
                const SizedBox(height: 10),
                FilledButton.icon(
                  onPressed: _busy
                      ? null
                      : () => _requireComment(() => api.disputeTransaction(claim.id, comment: _comment.text.trim())),
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.orange,
                    foregroundColor: Colors.white,
                    textStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                    minimumSize: const Size.fromHeight(48),
                  ),
                  icon: Icon(PhosphorIcons.arrowUUpLeft(), size: 20),
                  label: const Text('Dispute (send back to employee)'),
                ),
                const SizedBox(height: 10),
                FilledButton.icon(
                  onPressed: _busy
                      ? null
                      : () => _requireComment(() => api.rejectTransaction(claim.id, comment: _comment.text.trim())),
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.danger,
                    foregroundColor: Colors.white,
                    textStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                    minimumSize: const Size.fromHeight(48),
                  ),
                  icon: Icon(PhosphorIcons.xCircle(), size: 20),
                  label: const Text('Reject'),
                ),
              ],
              if (awaitingPayment) ...[
                const SizedBox(height: 16),
                TextField(
                  controller: _comment,
                  focusNode: _commentFocus,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: 'Remarks',
                    hintText: 'Payment reference, note… (optional)',
                  ),
                ),
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: _busy ? null : () => _act(() => api.markPaid(claim.id, remarks: _comment.text.trim())),
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.success,
                    foregroundColor: Colors.white,
                    textStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                    minimumSize: const Size.fromHeight(48),
                  ),
                  icon: Icon(PhosphorIcons.checkCircle(), size: 20),
                  label: const Text('Mark as paid'),
                ),
              ],
              const SizedBox(height: 20),
              Text('History', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ClaimHistoryList(history: claim.history ?? [], hideInternal: true),
            ],
          );
        },
      ),
    );
  }

  final _commentFocus = FocusNode();

  void _requireComment(Future<ExpenseClaim> Function() action) {
    if (_comment.text.trim().isEmpty) {
      _commentFocus.requestFocus();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please add a comment before disputing or rejecting')),
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

/// Lets whoever's holding the claim at its current stage either link the unmatched vendor
/// text to an existing known vendor, or confirm it's genuinely new — closing the loop the
/// plain warning banner used to leave dead-ended (see PETTY_CASH_PHASED_PLAN.md Phase 4).
class _VendorResolveCard extends ConsumerStatefulWidget {
  const _VendorResolveCard({
    required this.transactionId,
    required this.rawVendorText,
    required this.busy,
    required this.onResolve,
  });

  final int transactionId;
  final String rawVendorText;
  final bool busy;

  /// (vendorId, createNew) -- exactly one of vendorId or createNew=true is meaningful per call.
  final void Function(int? vendorId, bool createNew) onResolve;

  @override
  ConsumerState<_VendorResolveCard> createState() => _VendorResolveCardState();
}

class _VendorResolveCardState extends ConsumerState<_VendorResolveCard> {
  late Future<List<VendorRef>> _vendorsFuture;
  VendorRef? _selected;

  @override
  void initState() {
    super.initState();
    _vendorsFuture = ref.read(apiClientProvider).vendors();
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.warningSoft,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Unmatched vendor: "${widget.rawVendorText}" is not in the vendor list.'),
            const SizedBox(height: 10),
            FutureBuilder<List<VendorRef>>(
              future: _vendorsFuture,
              builder: (context, snapshot) {
                final vendors = snapshot.data ?? const <VendorRef>[];
                return Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<VendorRef>(
                        initialValue: _selected,
                        isExpanded: true,
                        hint: Text(snapshot.connectionState == ConnectionState.waiting ? 'Loading vendors…' : 'Link to existing vendor'),
                        items: vendors
                            .map((v) => DropdownMenuItem(value: v, child: Text(v.name, overflow: TextOverflow.ellipsis)))
                            .toList(),
                        onChanged: widget.busy ? null : (v) => setState(() => _selected = v),
                      ),
                    ),
                    const SizedBox(width: 8),
                    FilledButton(
                      onPressed: widget.busy || _selected == null
                          ? null
                          : () => widget.onResolve(_selected!.id, false),
                      child: const Text('Link'),
                    ),
                  ],
                );
              },
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerLeft,
              child: OutlinedButton(
                onPressed: widget.busy ? null : () => widget.onResolve(null, true),
                child: Text('Confirm "${widget.rawVendorText}" as a new vendor'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

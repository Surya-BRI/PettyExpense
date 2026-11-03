import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import 'package:intl/intl.dart';

import '../../utils/money.dart';
import '../../widgets/app_card.dart';
import '../../widgets/receipt_pages_view.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/claim_ui_helpers.dart';
import '../claims/claim_detail_screen.dart' show ClaimLineItemsList, claimDetailProvider;
import '../payments/payment_sheet.dart';
import '../payments/payments_screen.dart' show paymentsProvider;
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
  bool _showFullBill = false;

  @override
  void dispose() {
    _comment.dispose();
    _commentFocus.dispose();
    super.dispose();
  }

  Future<void> _act(Future<ExpenseClaim> Function() action, {bool leave = true}) async {
    setState(() => _busy = true);
    try {
      await action();
      ref.invalidate(approvalDetailProvider(widget.transactionId));
      // Department HOD steps are listed in the HOD's own queue.
      final queueStage = widget.stage == 'department_hod' ? 'hod' : widget.stage;
      ref.invalidate(approvalsQueueProvider(widget.stage));
      ref.invalidate(approvalsQueueProvider(queueStage));
      ref.invalidate(claimDetailProvider(widget.transactionId));
      ref.invalidate(approverHistoryProvider);
      if (!mounted) return;
      if (leave) {
        context.go('/approvals/$queueStage');
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Updated')));
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
          final pages = claim.receipt?.pageImageUrls ?? const <String>[];
          final total = claim.totalAmount ?? (claim.amount + claim.vatAmount);
          final awaitingThisStage =
              claim.status == 'submitted' && claim.currentStage == widget.stage;
          final withEmployee = claim.status == 'disputed';
          // Petty cash is settled from the fund at final approval -- only reimbursements get paid.
          final awaitingPayment = claim.status == 'approved' && claim.type != 'petty_cash';
          // At a department HOD step (e.g. IT HOD on a Sales bill) the reviewer approves only
          // the lines their department owns.
          final stageKey = claim.currentStageKey ?? '';
          final reviewDeptId = awaitingThisStage && widget.stage == 'department_hod' && stageKey.contains(':')
              ? int.tryParse(stageKey.split(':').last)
              : null;
          final deptLines = reviewDeptId == null
              ? const <ClaimLineItem>[]
              : claim.lineItems.where((l) => l.owningDepartmentId == reviewDeptId).toList();
          final linesTotal = claim.lineItems.fold(0.0, (sum, l) => sum + l.amount);
          final deptPart = deptLines.isEmpty || linesTotal <= 0
              ? null
              : total * deptLines.fold(0.0, (sum, l) => sum + l.amount) / linesTotal;
          final onlyDeptLines = deptPart != null && !_showFullBill;

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
                        StatusChip.forClaim(claim),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ClaimTypeTag(type: claim.type),
                    const SizedBox(height: 16),
                    MoneyBreakdownRow('Amount excl. VAT', formatMoney(claim.currency, claim.amount)),
                    const SizedBox(height: 6),
                    MoneyBreakdownRow('VAT', formatMoney(claim.currency, claim.vatAmount)),
                    const Divider(height: 20),
                    MoneyBreakdownRow('Total', formatMoney(claim.currency, total), emphasize: deptPart == null),
                    RegionTotalBreakdownRow(claim: claim, billTotal: total),
                    if (deptPart != null) ...[
                      const Divider(height: 20),
                      MoneyBreakdownRow(
                        'Your part (${deptLines.first.owningDepartmentName ?? 'department'})',
                        formatMoney(claim.currency, deptPart),
                        emphasize: true,
                      ),
                      if (claim.isConverted && claim.totalAmountBase != null && total > 0) ...[
                        const SizedBox(height: 6),
                        MoneyBreakdownRow(
                          'In ${claim.baseCurrency}',
                          formatMoney(claim.baseCurrency!, claim.totalAmountBase! * deptPart / total),
                        ),
                      ],
                    ],
                  ],
                ),
              ),
              if (claim.isMultiItem) ...[
                const SizedBox(height: 16),
                ClaimLineItemsList(claim: claim, onlyDepartmentId: onlyDeptLines ? reviewDeptId : null),
                if (deptPart != null)
                  Align(
                    alignment: Alignment.centerLeft,
                    child: TextButton(
                      onPressed: () => setState(() => _showFullBill = !_showFullBill),
                      child: Text(
                        _showFullBill
                            ? 'Show only your department\'s items'
                            : 'Show full bill (${claim.lineItems.length} items)',
                      ),
                    ),
                  ),
              ],
              if (pages.isNotEmpty) ...[
                const SizedBox(height: 16),
                AppCard(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        pages.length > 1 ? 'Receipt (${pages.length} pages)' : 'Receipt',
                        style: Theme.of(context).textTheme.titleSmall,
                      ),
                      const SizedBox(height: 10),
                      ReceiptPagesView.network(pages, height: 240),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 16),
              ClaimDetailsCard(
                title: 'Details',
                rows: [
                  ClaimDetailRow(
                    label: 'Invoice no.',
                    value: (claim.billNumber ?? '').trim().isEmpty ? '—' : claim.billNumber!.trim(),
                  ),
                  ClaimDetailRow(label: 'Employee', value: claim.employeeDisplay),
                  ClaimDetailRow(label: 'Bill currency', value: claim.currency),
                  ...claimConversionDetailRows(claim, total, showRate: true),
                  ClaimDetailRow(label: 'Category', value: claim.category),
                  if (claim.regionCode != null) ClaimDetailRow(label: 'Region', value: claim.regionCode!),
                  ClaimDetailRow(label: 'Bill date', value: _formatBillDate(claim.billDate)),
                  if (claim.submittedAt != null) ClaimDetailRow(label: 'Submitted', value: _formatSubmittedAt(claim.submittedAt)),
                  ClaimDetailRow(
                    label: 'Current stage',
                    value: claim.currentStageLabel,
                  ),
                  ClaimDetailRow(
                    label: 'Remarks',
                    value: (claim.remarks ?? '').trim().isEmpty ? '—' : claim.remarks!.trim(),
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
              if (withEmployee) ...[
                const SizedBox(height: 16),
                Material(
                  color: AppColors.warningSoft,
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(
                      'Sent back to the employee'
                      '${(claim.lastReturnEntry?.remarks ?? '').trim().isEmpty ? '' : ': ${claim.lastReturnEntry!.remarks}'}. '
                      'Approve and Reject return after they correct and resubmit.',
                    ),
                  ),
                ),
              ] else if (!awaitingThisStage && !awaitingPayment) ...[
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
                    label: Text(
                      requiresJustification
                          ? 'Approve (justify duplicate above)'
                          : deptPart != null
                              ? 'Approve ${deptLines.first.owningDepartmentName ?? 'your'} items'
                              : 'Approve',
                    ),
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
              if (claim.payment != null) ...[
                const SizedBox(height: 16),
                PaymentDetailsCard(payment: claim.payment!),
              ],
              if (awaitingPayment) ...[
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: _busy
                      ? null
                      : () async {
                          if (!await showRecordPaymentSheet(context, claim)) return;
                          ref.invalidate(paymentsProvider);
                          await _act(() => api.getApprovalTransaction(claim.id), leave: false);
                        },
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.success,
                    foregroundColor: Colors.white,
                    textStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                    minimumSize: const Size.fromHeight(48),
                  ),
                  icon: Icon(PhosphorIcons.money(), size: 20),
                  label: const Text('Record payment'),
                ),
              ],
              const SizedBox(height: 20),
              Text('History', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ClaimHistoryList(history: claim.history ?? [], stageLabels: claim.stageLabels),
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

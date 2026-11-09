import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/money.dart';
import '../../widgets/claim_ui_helpers.dart';

const kPaymentMethods = <String, String>{
  'bank_transfer': 'Bank transfer',
  'cash': 'Cash',
  'payroll': 'Payroll',
  'cheque': 'Cheque',
};

/// What the employee is owed, in the company's base currency.
(double, String) payableFor(ExpenseClaim claim) {
  if (claim.payableAmount != null && claim.payableCurrency != null) {
    return (claim.payableAmount!, claim.payableCurrency!);
  }
  if (claim.totalAmountBase != null && claim.baseCurrency != null) {
    return (claim.totalAmountBase!, claim.baseCurrency!);
  }
  return (claim.totalAmount ?? (claim.amount + claim.vatAmount), claim.currency);
}

/// Professional Signs (PCA PDF section 7): how an approved bill was paid.
const kPaymentProcesses = <String, (String, String)>{
  'bank': ('Process 1 · Cash withdrawal from bank', 'Cash withdrawn from the bank and paid out'),
  'accounts_petty_cash': ('Process 2 · Direct payment by Accounts', 'Paid directly by the Accounts Department'),
};

/// Opens the "Record payment" sheet; true once the payment is saved.
Future<bool> showRecordPaymentSheet(BuildContext context, ExpenseClaim claim) =>
    showRecordPaymentsSheet(context, [claim]);

/// One payment for several approved bills (same process/method, reference and date).
Future<bool> showRecordPaymentsSheet(BuildContext context, List<ExpenseClaim> claims) async {
  final saved = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    builder: (_) => _RecordPaymentSheet(claims: claims),
  );
  return saved ?? false;
}

class _RecordPaymentSheet extends ConsumerStatefulWidget {
  const _RecordPaymentSheet({required this.claims});

  final List<ExpenseClaim> claims;

  @override
  ConsumerState<_RecordPaymentSheet> createState() => _RecordPaymentSheetState();
}

class _RecordPaymentSheetState extends ConsumerState<_RecordPaymentSheet> {
  final _reference = TextEditingController();
  final _remarks = TextEditingController();
  String _method = 'bank_transfer';
  String _process = 'bank';

  bool get _byProcess => widget.claims.any((c) => c.paysByProcess);
  DateTime _date = DateUtils.dateOnly(DateTime.now());
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _reference.dispose();
    _remarks.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateUtils.dateOnly(DateTime.now()),
    );
    if (picked != null) setState(() => _date = picked);
  }

  Future<void> _save() async {
    final reference = _reference.text.trim();
    if (reference.isEmpty) {
      setState(() => _error = 'Enter the payment reference');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      final date = DateFormat('yyyy-MM-dd').format(_date);
      final remarks = _remarks.text.trim().isEmpty ? null : _remarks.text.trim();
      final method = _byProcess ? null : _method;
      final source = _byProcess ? _process : null;
      if (widget.claims.length == 1) {
        await api.recordPayment(
          claimId: widget.claims.single.id,
          method: method,
          source: source,
          reference: reference,
          paymentDate: date,
          remarks: remarks,
        );
      } else {
        final out = await api.recordPaymentBatch(
          claimIds: [for (final c in widget.claims) c.id],
          method: method,
          source: source,
          reference: reference,
          paymentDate: date,
          remarks: remarks,
        );
        if (out.skipped.isNotEmpty && mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('${out.paid} paid. Not paid: ${out.skipped.join('; ')}')),
          );
        }
      }
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final claims = widget.claims;
    final currency = payableFor(claims.first).$2;
    final amount = claims.fold(0.0, (sum, c) => sum + payableFor(c).$1);
    final first = claims.first;
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 20, 20, 20 + MediaQuery.viewInsetsOf(context).bottom),
      child: SingleChildScrollView(
        child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('Record payment', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 4),
          Text(
            claims.length == 1
                ? 'Claim #${first.id} · ${first.employeeDisplay}'
                    '${first.type == 'petty_cash' && first.paysByProcess ? ' · petty cash (refills their PCA)' : ''}'
                : '${claims.length} bills · one payment',
            style: const TextStyle(color: AppColors.textSecondary),
          ),
          const SizedBox(height: 16),
          MoneyBreakdownRow('Amount to pay', formatMoney(currency, amount), emphasize: true),
          const SizedBox(height: 16),
          if (_byProcess) ...[
            const Text('How was it paid?', style: TextStyle(fontWeight: FontWeight.w700)),
            RadioGroup<String>(
              groupValue: _process,
              onChanged: (v) => setState(() => _process = v ?? _process),
              child: Column(
                children: [
                  for (final e in kPaymentProcesses.entries)
                    RadioListTile<String>(
                      value: e.key,
                      enabled: !_busy,
                      contentPadding: EdgeInsets.zero,
                      title: Text(e.value.$1, style: const TextStyle(fontWeight: FontWeight.w600)),
                      subtitle: Text(e.value.$2),
                    ),
                ],
              ),
            ),
          ] else
            DropdownButtonFormField<String>(
              initialValue: _method,
              decoration: const InputDecoration(labelText: 'Payment method'),
              items: [
                for (final e in kPaymentMethods.entries) DropdownMenuItem(value: e.key, child: Text(e.value)),
              ],
              onChanged: _busy ? null : (v) => setState(() => _method = v ?? _method),
            ),
          const SizedBox(height: 12),
          TextField(
            controller: _reference,
            enabled: !_busy,
            decoration: InputDecoration(
              labelText: 'Payment reference *',
              hintText: _byProcess
                  ? (_process == 'bank' ? 'Bank withdrawal no.' : 'Payment voucher / transfer no.')
                  : 'Transfer no., cheque no., payroll batch…',
            ),
          ),
          const SizedBox(height: 12),
          InkWell(
            onTap: _busy ? null : _pickDate,
            child: InputDecorator(
              decoration: const InputDecoration(labelText: 'Payment date'),
              child: Text(DateFormat('d MMM yyyy').format(_date)),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _remarks,
            enabled: !_busy,
            maxLines: 2,
            decoration: const InputDecoration(labelText: 'Remarks (optional)'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: AppColors.danger)),
          ],
          const SizedBox(height: 20),
          FilledButton.icon(
            onPressed: _busy ? null : _save,
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.success,
              foregroundColor: Colors.white,
              textStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
              minimumSize: const Size.fromHeight(48),
            ),
            icon: Icon(PhosphorIcons.checkCircle(), size: 20),
            label: Text(claims.length == 1 ? 'Mark as paid' : 'Mark ${claims.length} as paid'),
          ),
        ],
        ),
      ),
    );
  }
}

/// How the claim was paid — shown on claim and approval detail once paid.
class PaymentDetailsCard extends StatelessWidget {
  const PaymentDetailsCard({super.key, required this.payment});

  final PaymentRecord payment;

  @override
  Widget build(BuildContext context) {
    final day = DateTime.tryParse(payment.paymentDate ?? '');
    return ClaimDetailsCard(
      title: 'Payment',
      rows: [
        ClaimDetailRow(label: 'Amount paid', value: formatMoney(payment.currency, payment.amount)),
        ClaimDetailRow(label: 'Method', value: payment.methodLabel),
        ClaimDetailRow(label: 'Reference', value: payment.reference),
        ClaimDetailRow(label: 'Paid on', value: day == null ? '—' : DateFormat('d MMM yyyy').format(day)),
        if ((payment.paidByName ?? '').isNotEmpty) ClaimDetailRow(label: 'Recorded by', value: payment.paidByName!),
        if ((payment.remarks ?? '').isNotEmpty) ClaimDetailRow(label: 'Remarks', value: payment.remarks!),
      ],
    );
  }
}

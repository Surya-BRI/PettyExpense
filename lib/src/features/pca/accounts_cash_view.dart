// The Accounts Department's own petty cash (Professional Signs, PCA PDF section 6).
//
// "Direct payment by Accounts Department" (Process 2) takes from it; the Accounts Manager
// refills it from the bank; Admin sets its amount. Shown as a tab on the Advances screen for
// the Accounts Manager, Accounts and Admin.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/money.dart';

final accountsCashProvider = FutureProvider.autoDispose.family<AccountsCash, int>((ref, regionId) {
  return ref.watch(apiClientProvider).accountsCash(regionId);
});

class AccountsCashView extends ConsumerWidget {
  const AccountsCashView({super.key, required this.regionId});

  final int regionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(accountsCashProvider(regionId));
    return RefreshIndicator(
      onRefresh: () => ref.refresh(accountsCashProvider(regionId).future),
      child: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => ListView(
          padding: const EdgeInsets.all(24),
          children: [Text('$e', style: const TextStyle(color: AppColors.danger))],
        ),
        data: (cash) => ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
          children: [
            _BalanceCard(cash: cash),
            const SizedBox(height: 12),
            Row(
              children: [
                if (cash.canRefill && cash.configured)
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: cash.toRefill <= 0
                          ? null
                          : () async {
                              final done = await showModalBottomSheet<bool>(
                                context: context,
                                isScrollControlled: true,
                                builder: (_) => _RefillSheet(cash: cash),
                              );
                              if (done == true) ref.invalidate(accountsCashProvider(regionId));
                            },
                      style: FilledButton.styleFrom(
                        backgroundColor: AppColors.success,
                        minimumSize: const Size.fromHeight(46),
                      ),
                      icon: Icon(PhosphorIcons.arrowCounterClockwise(), size: 18),
                      label: const Text('Refill from bank'),
                    ),
                  ),
                if (cash.canRefill && cash.configured && cash.canSet) const SizedBox(width: 10),
                if (cash.canSet)
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () async {
                        final done = await showDialog<bool>(
                          context: context,
                          builder: (_) => _SetAmountDialog(cash: cash),
                        );
                        if (done == true) ref.invalidate(accountsCashProvider(regionId));
                      },
                      style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(46)),
                      icon: Icon(PhosphorIcons.pencilSimple(), size: 18),
                      label: Text(cash.configured ? 'Change amount' : 'Set amount'),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 20),
            const Text('Recent movements', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
            const SizedBox(height: 8),
            if (cash.entries.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: Text('Nothing yet.', style: TextStyle(color: AppColors.textSecondary)),
              )
            else
              for (final e in cash.entries) _EntryTile(entry: e, currency: cash.currency),
          ],
        ),
      ),
    );
  }
}

class _BalanceCard extends StatelessWidget {
  const _BalanceCard({required this.cash});

  final AccountsCash cash;

  @override
  Widget build(BuildContext context) {
    if (!cash.configured) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Icon(PhosphorIcons.warningCircle(), color: AppColors.orange),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  cash.canSet
                      ? 'Not set up yet. Set its amount so Accounts can pay by Process 2 '
                          '(direct payment by Accounts Department).'
                      : 'Not set up yet. Until the Accounts Manager or Admin sets its amount, '
                          'pay by Process 1 (cash withdrawal from bank).',
                ),
              ),
            ],
          ),
        ),
      );
    }
    final used = cash.limit <= 0 ? 0.0 : (cash.toRefill / cash.limit).clamp(0.0, 1.0);
    final barColor = cash.low ? AppColors.danger : (used >= 0.5 ? AppColors.orange : AppColors.success);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Accounts Department petty cash',
                style: TextStyle(color: AppColors.textSecondary, fontWeight: FontWeight.w600)),
            const SizedBox(height: 6),
            Text(
              formatMoney(cash.currency, cash.available),
              style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: AppColors.darkBlue),
            ),
            Text('left of ${formatMoney(cash.currency, cash.limit)}',
                style: const TextStyle(color: AppColors.textSecondary)),
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: used,
                minHeight: 8,
                color: barColor,
                backgroundColor: AppColors.lightBlue,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                _Figure(label: 'Paid out (Process 2)', value: formatMoney(cash.currency, cash.paidOut)),
                _Figure(label: 'Refilled', value: formatMoney(cash.currency, cash.refilled)),
                _Figure(
                  label: 'To refill',
                  value: formatMoney(cash.currency, cash.toRefill),
                  color: cash.toRefill > 0 ? AppColors.orange : null,
                ),
              ],
            ),
            if (cash.low) ...[
              const SizedBox(height: 10),
              Text(
                'Running low: refill it from the bank.',
                style: TextStyle(color: AppColors.danger, fontWeight: FontWeight.w600),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _Figure extends StatelessWidget {
  const _Figure({required this.label, required this.value, this.color});

  final String label;
  final String value;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
          const SizedBox(height: 2),
          Text(value, style: TextStyle(fontWeight: FontWeight.w700, color: color)),
        ],
      ),
    );
  }
}

class _EntryTile extends StatelessWidget {
  const _EntryTile({required this.entry, required this.currency});

  final AccountsCashEntry entry;
  final String currency;

  @override
  Widget build(BuildContext context) {
    final (icon, color, title, sign) = switch (entry.kind) {
      'payout' => (
          PhosphorIcons.arrowUpRight(),
          AppColors.orange,
          entry.transactionId != null
              ? 'Paid bill #${entry.transactionId}${entry.employeeName != null ? ' · ${entry.employeeName}' : ''}'
              : 'Paid advance request #${entry.topupId ?? ''}',
          '−',
        ),
      'refill' => (PhosphorIcons.arrowDownLeft(), AppColors.success, 'Refilled from bank', '+'),
      _ => (PhosphorIcons.pencilSimple(), AppColors.textSecondary, 'Amount changed', entry.amount < 0 ? '−' : '+'),
    };
    final sub = [
      if (entry.date != null) DateFormat('d MMM yyyy').format(entry.date!),
      if (entry.reference != null) 'ref ${entry.reference}',
      if (entry.actorName != null) entry.actorName!,
      if (entry.remarks != null && entry.kind != 'payout') entry.remarks!,
    ].join(' · ');
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Icon(icon, color: color),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: sub.isEmpty ? null : Text(sub),
        trailing: Text(
          '$sign${formatMoney(currency, entry.amount.abs())}',
          style: TextStyle(fontWeight: FontWeight.w700, color: color),
        ),
      ),
    );
  }
}

class _SetAmountDialog extends ConsumerStatefulWidget {
  const _SetAmountDialog({required this.cash});

  final AccountsCash cash;

  @override
  ConsumerState<_SetAmountDialog> createState() => _SetAmountDialogState();
}

class _SetAmountDialogState extends ConsumerState<_SetAmountDialog> {
  late final _amount = TextEditingController(
    text: widget.cash.limit > 0 ? widget.cash.limit.toStringAsFixed(2) : '',
  );
  final _remarks = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _amount.dispose();
    _remarks.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final amount = double.tryParse(_amount.text.replaceAll(',', '').trim());
    if (amount == null || amount < 0) {
      setState(() => _error = 'Enter the amount');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).setAccountsCash(
            widget.cash.regionId,
            amount,
            remarks: _remarks.text.trim().isEmpty ? null : _remarks.text.trim(),
          );
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Accounts Department petty cash'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: _amount,
            enabled: !_busy,
            autofocus: true,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: InputDecoration(labelText: 'Amount (${widget.cash.currency}) *'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _remarks,
            enabled: !_busy,
            decoration: const InputDecoration(labelText: 'Reason (optional)'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: AppColors.danger)),
          ],
        ],
      ),
      actions: [
        TextButton(
          onPressed: _busy ? null : () => Navigator.of(context).pop(false),
          child: const Text('Cancel'),
        ),
        FilledButton(onPressed: _busy ? null : _save, child: const Text('Save')),
      ],
    );
  }
}

class _RefillSheet extends ConsumerStatefulWidget {
  const _RefillSheet({required this.cash});

  final AccountsCash cash;

  @override
  ConsumerState<_RefillSheet> createState() => _RefillSheetState();
}

class _RefillSheetState extends ConsumerState<_RefillSheet> {
  late final _amount = TextEditingController(text: widget.cash.toRefill.toStringAsFixed(2));
  final _reference = TextEditingController();
  final _remarks = TextEditingController();
  DateTime _date = DateUtils.dateOnly(DateTime.now());
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _amount.dispose();
    _reference.dispose();
    _remarks.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final amount = double.tryParse(_amount.text.replaceAll(',', '').trim());
    if (amount == null || amount <= 0) {
      setState(() => _error = 'Enter the amount put back');
      return;
    }
    final reference = _reference.text.trim();
    if (reference.isEmpty) {
      setState(() => _error = 'Enter the bank reference');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).refillAccountsCash(
            widget.cash.regionId,
            amount: amount,
            reference: reference,
            refillDate: DateFormat('yyyy-MM-dd').format(_date),
            remarks: _remarks.text.trim().isEmpty ? null : _remarks.text.trim(),
          );
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cash = widget.cash;
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 20, 20, 20 + MediaQuery.viewInsetsOf(context).bottom),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Refill from bank', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(
              '${formatMoney(cash.currency, cash.toRefill)} paid out and not refilled yet',
              style: const TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _amount,
              enabled: !_busy,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(labelText: 'Amount (${cash.currency}) *'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _reference,
              enabled: !_busy,
              decoration: const InputDecoration(
                labelText: 'Bank reference *',
                hintText: 'Withdrawal or transfer number',
              ),
            ),
            const SizedBox(height: 12),
            InkWell(
              onTap: _busy
                  ? null
                  : () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: _date,
                        firstDate: DateTime.now().subtract(const Duration(days: 365)),
                        lastDate: DateUtils.dateOnly(DateTime.now()),
                      );
                      if (picked != null) setState(() => _date = picked);
                    },
              child: InputDecorator(
                decoration: const InputDecoration(labelText: 'Date'),
                child: Text(DateFormat('d MMM yyyy').format(_date)),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _remarks,
              enabled: !_busy,
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
                minimumSize: const Size.fromHeight(48),
              ),
              icon: Icon(PhosphorIcons.checkCircle(), size: 20),
              label: const Text('Record refill'),
            ),
          ],
        ),
      ),
    );
  }
}

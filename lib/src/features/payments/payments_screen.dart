import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/money.dart';
import '../../widgets/app_nav_drawer.dart';
import '../../widgets/brand_app_bar.dart';
import 'payment_sheet.dart';

typedef _PaymentsQuery = ({String status, String? regionCode});

final paymentsProvider = FutureProvider.autoDispose.family<PaymentsPage, _PaymentsQuery>((ref, q) {
  return ref.watch(apiClientProvider).listPayments(status: q.status, regionCode: q.regionCode, limit: 200);
});

final _paymentRegionsProvider = FutureProvider.autoDispose<List<RegionConfig>>((ref) {
  return ref.watch(apiClientProvider).listRegions();
});

/// Finance Manager / Admin: approved reimbursements waiting for payment, and paid ones.
class PaymentsScreen extends ConsumerStatefulWidget {
  const PaymentsScreen({super.key});

  @override
  ConsumerState<PaymentsScreen> createState() => _PaymentsScreenState();
}

class _PaymentsScreenState extends ConsumerState<PaymentsScreen> {
  String _status = 'unpaid';
  String? _region;

  _PaymentsQuery get _query => (status: _status, regionCode: _region);

  Future<void> _pay(ExpenseClaim claim) async {
    if (!await showRecordPaymentSheet(context, claim)) return;
    ref.invalidate(paymentsProvider);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Claim #${claim.id} marked paid. ${claim.employeeDisplay} has been notified.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(paymentsProvider(_query));
    final regions = ref.watch(_paymentRegionsProvider).maybeWhen(data: (r) => r, orElse: () => const <RegionConfig>[]);

    return Scaffold(
      drawer: const AppNavDrawer(),
      appBar: const BrandAppBar(title: 'Payments', showNotificationAction: false),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'unpaid', label: Text('Waiting for payment')),
                ButtonSegment(value: 'paid', label: Text('Paid')),
              ],
              selected: {_status},
              onSelectionChanged: (s) => setState(() => _status = s.first),
            ),
          ),
          if (regions.length > 1)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 10, 16, 0),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    for (final code in [null, ...regions.map((r) => r.regionCode)])
                      Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: ChoiceChip(
                          label: Text(code ?? 'All companies'),
                          selected: _region == code,
                          onSelected: (_) => setState(() => _region = code),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          Expanded(
            child: async.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(
                child: Padding(padding: const EdgeInsets.all(24), child: Text('$e', textAlign: TextAlign.center)),
              ),
              data: (page) => RefreshIndicator(
                onRefresh: () async => ref.invalidate(paymentsProvider(_query)),
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _TotalsBar(page: page, paid: _status == 'paid'),
                    const SizedBox(height: 12),
                    if (page.items.isEmpty)
                      Padding(
                        padding: const EdgeInsets.all(32),
                        child: Text(
                          _status == 'paid' ? 'No paid claims yet.' : 'No approved claims waiting for payment.',
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: AppColors.textSecondary),
                        ),
                      ),
                    for (final c in page.items) ...[
                      _PaymentTile(
                        claim: c,
                        onOpen: () => context.push('/approvals/finance_manager/${c.id}'),
                        onPay: _status == 'unpaid' ? () => _pay(c) : null,
                      ),
                      const SizedBox(height: 10),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _TotalsBar extends StatelessWidget {
  const _TotalsBar({required this.page, required this.paid});

  final PaymentsPage page;
  final bool paid;

  @override
  Widget build(BuildContext context) {
    final amounts = page.totals.entries.map((e) => formatMoney(e.key, e.value)).join(' · ');
    return Material(
      color: paid ? AppColors.darkBlue.withValues(alpha: 0.08) : AppColors.warningSoft,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            Expanded(
              child: Text(
                '${page.total} ${page.total == 1 ? 'claim' : 'claims'} ${paid ? 'paid' : 'to pay'}',
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
            if (amounts.isNotEmpty) Text(amounts, style: const TextStyle(fontWeight: FontWeight.w700)),
          ],
        ),
      ),
    );
  }
}

class _PaymentTile extends StatelessWidget {
  const _PaymentTile({required this.claim, required this.onOpen, this.onPay});

  final ExpenseClaim claim;
  final VoidCallback onOpen;
  final VoidCallback? onPay;

  @override
  Widget build(BuildContext context) {
    final (amount, currency) = payableFor(claim);
    final billTotal = claim.totalAmount ?? (claim.amount + claim.vatAmount);
    final payment = claim.payment;
    final approved = DateTime.tryParse(claim.decidedAt ?? '');
    final paidOn = DateTime.tryParse(payment?.paymentDate ?? '');
    final subtitle = [
      claim.employeeDisplay,
      if (claim.regionCode != null) claim.regionCode!,
      if (payment == null && approved != null) 'approved ${DateFormat('d MMM').format(approved.toLocal())}',
      if (payment != null && paidOn != null) 'paid ${DateFormat('d MMM yyyy').format(paidOn)}',
    ].join(' · ');
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onOpen,
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            border: Border.all(color: AppColors.divider),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      '#${claim.id} · ${claim.vendor}',
                      style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14.5),
                    ),
                  ),
                  Text(formatMoney(currency, amount), style: const TextStyle(fontWeight: FontWeight.w700)),
                ],
              ),
              const SizedBox(height: 4),
              Text(subtitle, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12.5)),
              if (currency.toUpperCase() != claim.currency.toUpperCase())
                Text(
                  'Bill ${formatMoney(claim.currency, billTotal)}',
                  style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                ),
              if (payment != null)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    '${payment.methodLabel} · ref ${payment.reference}',
                    style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600, color: AppColors.darkBlue),
                  ),
                ),
              if (onPay != null) ...[
                const SizedBox(height: 10),
                Align(
                  alignment: Alignment.centerRight,
                  child: FilledButton.icon(
                    onPressed: onPay,
                    style: FilledButton.styleFrom(backgroundColor: AppColors.success, foregroundColor: Colors.white),
                    icon: Icon(PhosphorIcons.money(), size: 18),
                    label: const Text('Record payment'),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

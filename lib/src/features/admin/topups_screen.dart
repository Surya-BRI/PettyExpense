import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../api/enums.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/money.dart';
import '../../widgets/app_nav_drawer.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/pca_fund_figures.dart';
import '../../widgets/shimmer_box.dart';
import '../authentication/auth_controller.dart';
import 'admin_providers.dart';
import 'my_funds_screen.dart';

final topupsProvider = FutureProvider.autoDispose<List<TopupRequest>>((ref) {
  return ref.watch(apiClientProvider).listTopups();
});

String topupStatusLabel(String status) {
  switch (status) {
    case 'submitted':
      return 'Pending Accounts';
    case 'verified':
      return 'Pending Finance';
    case 'approved':
      return 'Approved';
    case 'rejected':
      return 'Rejected';
    case 'returned':
      return 'Returned to HOD';
    default:
      return status;
  }
}

String topupActionLabel(String action) {
  switch (action) {
    case 'requested':
      return 'Requested';
    case 'verified':
      return 'Verified by Accounts';
    case 'returned':
      return 'Returned to HOD';
    case 'approved':
      return 'Approved';
    case 'rejected':
      return 'Rejected';
    default:
      return action;
  }
}

void invalidateFundProviders(WidgetRef ref) {
  ref.invalidate(topupsProvider);
  ref.invalidate(myFundsProvider);
  ref.invalidate(adminFundsProvider);
  ref.invalidate(departmentFundsProvider);
}

class TopupsScreen extends ConsumerWidget {
  const TopupsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final role = UserRoleX.fromJson(ref.watch(authControllerProvider).user?.role);
    final isHod = role == UserRole.hod;
    final topupsAsync = ref.watch(topupsProvider);
    final fundsAsync = isHod ? ref.watch(myFundsProvider) : null;

    return Scaffold(
      backgroundColor: AppColors.background,
      drawer: const AppNavDrawer(),
      appBar: BrandAppBar(title: isHod ? 'Funds' : 'Top-ups', automaticallyImplyLeading: true),
      // Admin raises top-ups on a department's behalf (HOD away, or no HOD).
      floatingActionButton: role == UserRole.admin
          ? FloatingActionButton.extended(
              onPressed: () async {
                await Navigator.of(context).push(MaterialPageRoute(builder: (_) => const RaiseTopupScreen()));
                invalidateFundProviders(ref);
              },
              icon: Icon(PhosphorIcons.plus(), size: 18),
              label: const Text('Request top-up'),
            )
          : null,
      body: isHod
          ? _hodBody(context, ref, fundsAsync!, topupsAsync)
          : topupsAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('$e')),
              data: (items) {
                if (items.isEmpty) {
                  return const Center(child: Text('No top-up requests yet'));
                }
                return ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
                  itemCount: items.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 10),
                  itemBuilder: (context, i) => TopupRequestTile(request: items[i]),
                );
              },
            ),
    );
  }

  Widget _hodBody(
    BuildContext context,
    WidgetRef ref,
    AsyncValue<List<PettyCashFund>> fundsAsync,
    AsyncValue<List<TopupRequest>> topupsAsync,
  ) {
    if ((fundsAsync.isLoading && !fundsAsync.hasValue) || (topupsAsync.isLoading && !topupsAsync.hasValue)) {
      return const Center(child: CircularProgressIndicator());
    }
    if (fundsAsync.hasError) return Center(child: Text('${fundsAsync.error}'));
    if (topupsAsync.hasError) return Center(child: Text('${topupsAsync.error}'));

    final funds =
        [
          for (final f in fundsAsync.valueOrNull ?? const <PettyCashFund>[])
            if (f.ownerType == 'department') f,
        ]..sort((a, b) {
          final ai = kAdminRegionOrder.indexOf((a.regionCode ?? '').toUpperCase());
          final bi = kAdminRegionOrder.indexOf((b.regionCode ?? '').toUpperCase());
          return (ai < 0 ? 99 : ai).compareTo(bi < 0 ? 99 : bi);
        });
    final topups = topupsAsync.valueOrNull ?? const <TopupRequest>[];

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
      children: [
        if (funds.isEmpty)
          const Padding(
            padding: EdgeInsets.fromLTRB(8, 12, 8, 20),
            child: Text(
              'No petty cash is set up for your department yet. Ask Admin to set an approved limit.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textSecondary),
            ),
          )
        else
          for (final fund in funds) ...[
            _HodFundCard(
              fund: fund,
              onRequestTopup: () async {
                await Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => RaiseTopupScreen(fundId: fund.id, regionId: fund.regionId, fund: fund),
                  ),
                );
                invalidateFundProviders(ref);
              },
            ),
            const SizedBox(height: 12),
          ],
        const SizedBox(height: 8),
        const Text(
          'Top-ups',
          style: TextStyle(color: AppColors.darkBlue, fontWeight: FontWeight.w800, fontSize: 13, letterSpacing: 0.3),
        ),
        const SizedBox(height: 8),
        if (topups.isEmpty)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 18),
            decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(14)),
            child: const Text('No top-up requests yet', style: TextStyle(color: AppColors.textSecondary)),
          )
        else
          for (var i = 0; i < topups.length; i++) ...[
            if (i > 0) const SizedBox(height: 10),
            TopupRequestTile(request: topups[i]),
          ],
      ],
    );
  }
}

class _HodFundCard extends StatelessWidget {
  const _HodFundCard({required this.fund, required this.onRequestTopup});

  final PettyCashFund fund;
  final VoidCallback onRequestTopup;

  @override
  Widget build(BuildContext context) {
    final company = fundCompanyName(fund);
    final dept = (fund.departmentName ?? 'Department').trim();
    final code = (fund.regionCode ?? '').trim().toUpperCase();
    return Material(
      color: AppColors.card,
      elevation: 0,
      borderRadius: BorderRadius.circular(16),
      clipBehavior: Clip.antiAlias,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              company,
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18, height: 1.2, color: AppColors.darkBlue),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 6,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                if (code.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(color: AppColors.lightBlue, borderRadius: BorderRadius.circular(6)),
                    child: Text(
                      code,
                      style: const TextStyle(
                        color: AppColors.darkBlue,
                        fontWeight: FontWeight.w700,
                        fontSize: 11,
                        letterSpacing: 0.4,
                      ),
                    ),
                  ),
                Text('$dept petty cash', style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
              ],
            ),
            const SizedBox(height: 14),
            PcaFundFigures(fund: fund),
            const SizedBox(height: 14),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: onRequestTopup,
                icon: Icon(PhosphorIcons.plus(), size: 16),
                label: const Text('Request top-up'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class TopupRequestTile extends ConsumerWidget {
  const TopupRequestTile({super.key, required this.request});

  final TopupRequest request;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final role = UserRoleX.fromJson(ref.watch(authControllerProvider).user?.role);
    final canVerify = role == UserRole.accountant || role == UserRole.admin;
    final canDecide = role == UserRole.financeManager || role == UserRole.admin;
    final t = request;
    final currency = t.fund?.currency ?? '';
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              formatMoney(currency, t.amount),
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18, color: AppColors.darkBlue),
            ),
            const SizedBox(height: 4),
            if (t.fund != null)
              Text(fundCompanyName(t.fund!), style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
            const SizedBox(height: 2),
            Text(
              [t.fund?.departmentName, t.requesterName, topupStatusLabel(t.status)].whereType<String>().join(' · '),
              style: const TextStyle(color: AppColors.textSecondary),
            ),
            if (t.transactionIds.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                '${t.transactionIds.length} bill${t.transactionIds.length == 1 ? '' : 's'} linked',
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
              ),
            ],
            if (t.paymentReference != null && t.paymentReference!.trim().isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                'Payment ${t.paymentReference}',
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
              ),
            ],
            if (t.remarks != null && t.remarks!.trim().isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(t.remarks!, style: const TextStyle(fontSize: 13)),
            ],
            if (t.status == 'returned' && (t.returnReason ?? '').trim().isNotEmpty) ...[
              const SizedBox(height: 10),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(color: AppColors.warningSoft, borderRadius: BorderRadius.circular(10)),
                child: Text(
                  'Returned: ${t.returnReason!.trim()}. Fix it and raise a new request.',
                  style: const TextStyle(fontSize: 13),
                ),
              ),
            ],
            if (t.history.isNotEmpty) _TopupHistory(entries: t.history),
            if (canVerify && t.status == 'submitted') ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: FilledButton(
                      onPressed: () =>
                          runTopupAction(context, ref, () => ref.read(apiClientProvider).verifyTopup(t.id)),
                      child: const Text('Verify'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => returnTopup(context, ref, t.id),
                      child: const Text('Return to HOD'),
                    ),
                  ),
                ],
              ),
            ],
            if (canDecide && (t.status == 'verified' || (role == UserRole.admin && t.status == 'submitted'))) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: FilledButton(
                      onPressed: () => approveTopup(context, ref, t.id),
                      child: const Text('Approve'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => runTopupAction(
                        context,
                        ref,
                        () => ref.read(apiClientProvider).decideTopup(t.id, approve: false),
                      ),
                      child: const Text('Reject'),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

Future<void> runTopupAction(BuildContext context, WidgetRef ref, Future<void> Function() action) async {
  try {
    await action();
    invalidateFundProviders(ref);
  } catch (e) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }
}

/// Accounts sends a top-up back to the HOD; the reason is required.
Future<void> returnTopup(BuildContext context, WidgetRef ref, int id) async {
  final reason = await showDialog<String>(context: context, builder: (_) => const _ReturnReasonDialog());
  if (reason == null || reason.isEmpty || !context.mounted) return;
  await runTopupAction(context, ref, () => ref.read(apiClientProvider).returnTopup(id, remarks: reason));
}

class _ReturnReasonDialog extends StatefulWidget {
  const _ReturnReasonDialog();

  @override
  State<_ReturnReasonDialog> createState() => _ReturnReasonDialogState();
}

class _ReturnReasonDialogState extends State<_ReturnReasonDialog> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final text = _controller.text.trim();
    return AlertDialog(
      title: const Text('Return to HOD'),
      content: TextField(
        controller: _controller,
        autofocus: true,
        maxLines: 3,
        onChanged: (_) => setState(() {}),
        decoration: const InputDecoration(labelText: 'Reason *', hintText: 'e.g. Receipt missing for one bill'),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Cancel')),
        FilledButton(
          onPressed: text.isEmpty ? null : () => Navigator.of(context).pop(text),
          child: const Text('Return'),
        ),
      ],
    );
  }
}

/// Collapsible audit trail of a top-up: who did what, when, and why.
class _TopupHistory extends StatelessWidget {
  const _TopupHistory({required this.entries});

  final List<TopupHistoryEntry> entries;

  String _when(DateTime? at) {
    if (at == null) return '';
    final l = at.toLocal();
    String two(int n) => n.toString().padLeft(2, '0');
    return '${two(l.day)}/${two(l.month)}/${l.year} ${two(l.hour)}:${two(l.minute)}';
  }

  @override
  Widget build(BuildContext context) {
    return Theme(
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        childrenPadding: const EdgeInsets.only(bottom: 4),
        title: Text(
          'History (${entries.length})',
          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.darkBlue),
        ),
        children: [
          for (final h in entries.reversed)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 5),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          [topupActionLabel(h.action), if ((h.actorName ?? '').isNotEmpty) h.actorName!].join(' · '),
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                        ),
                        if ((h.comment ?? '').trim().isNotEmpty)
                          Text(
                            h.comment!.trim(),
                            style: const TextStyle(fontSize: 12.5, color: AppColors.textSecondary),
                          ),
                      ],
                    ),
                  ),
                  Text(_when(h.at), style: const TextStyle(fontSize: 11.5, color: AppColors.textSecondary)),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

Future<void> approveTopup(BuildContext context, WidgetRef ref, int id) async {
  final refText = await showModalBottomSheet<String>(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.card,
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
    builder: (ctx) => const _PaymentRefSheet(),
  );
  if (refText == null || !context.mounted) return;
  await runTopupAction(
    context,
    ref,
    () =>
        ref.read(apiClientProvider).decideTopup(id, approve: true, paymentReference: refText.isEmpty ? null : refText),
  );
}

class _PaymentRefSheet extends StatefulWidget {
  const _PaymentRefSheet();

  @override
  State<_PaymentRefSheet> createState() => _PaymentRefSheetState();
}

class _PaymentRefSheetState extends State<_PaymentRefSheet> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 16, 20, 20 + MediaQuery.viewInsetsOf(context).bottom),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Approve replenishment', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
          const SizedBox(height: 8),
          const Text(
            'Optional payment reference for the common bank account.',
            style: TextStyle(color: AppColors.textSecondary),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _controller,
            decoration: const InputDecoration(labelText: 'Payment reference'),
          ),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(_controller.text.trim()),
            child: const Text('Approve'),
          ),
        ],
      ),
    );
  }
}

class RaiseTopupScreen extends ConsumerStatefulWidget {
  const RaiseTopupScreen({super.key, this.fundId, this.regionId, this.fund});

  final int? fundId;
  final int? regionId;

  /// The fund the HOD tapped "Request top-up" on: the screen then skips loading funds and
  /// goes straight to that fund's bills.
  final PettyCashFund? fund;

  @override
  ConsumerState<RaiseTopupScreen> createState() => _RaiseTopupScreenState();
}

class _RaiseTopupScreenState extends ConsumerState<RaiseTopupScreen> {
  List<PettyCashFund> _funds = const [];
  // Admin only: raises for any department, one company at a time (loading every fund in
  // every company at once is slow).
  List<RegionConfig> _regions = const [];
  int? _adminRegionId;
  List<ReplenishableBill> _bills = const [];
  final Set<int> _selected = {};
  int? _fundId;
  final _remarks = TextEditingController();
  bool _busy = false;
  bool _loading = true;
  bool _loadingBills = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _remarks.dispose();
    super.dispose();
  }

  double get _amount => _bills.where((b) => _selected.contains(b.id)).fold(0, (sum, b) => sum + b.amount);

  PettyCashFund? _defaultFund(List<PettyCashFund> depts) {
    if (depts.isEmpty) return null;
    if (widget.fundId != null) {
      for (final f in depts) {
        if (f.id == widget.fundId) return f;
      }
    }
    final user = ref.read(authControllerProvider).user;
    final region = (user?.regionCode ?? '').toUpperCase();
    final deptId = user?.departmentId;
    if (deptId != null && region.isNotEmpty) {
      for (final f in depts) {
        if (f.departmentId == deptId && (f.regionCode ?? '').toUpperCase() == region) return f;
      }
    }
    if (widget.regionId != null) {
      for (final f in depts) {
        if (f.regionId == widget.regionId && (deptId == null || f.departmentId == deptId)) return f;
      }
    }
    if (deptId != null) {
      for (final f in depts) {
        if (f.departmentId == deptId) return f;
      }
    }
    if (region.isNotEmpty) {
      for (final f in depts) {
        if ((f.regionCode ?? '').toUpperCase() == region) return f;
      }
    }
    return depts.first;
  }

  String _fundLabel(PettyCashFund f) => fundCompanyLabel(f);

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final role = UserRoleX.fromJson(ref.read(authControllerProvider).user?.role);
      final api = ref.read(apiClientProvider);
      List<PettyCashFund> funds;
      if (widget.fund != null && role != UserRole.admin) {
        funds = [widget.fund!]; // came from the fund's card: nothing else to load
      } else if (role == UserRole.admin) {
        if (_regions.isEmpty) {
          _regions = await api.listRegions();
          final current = (ref.read(authControllerProvider).user?.regionCode ?? '').toUpperCase();
          _adminRegionId ??=
              widget.regionId ??
              _regions
                  .cast<RegionConfig?>()
                  .firstWhere(
                    (r) => r!.regionCode.toUpperCase() == current,
                    orElse: () => _regions.isEmpty ? null : _regions.first,
                  )
                  ?.id;
        }
        funds = _adminRegionId == null
            ? const []
            : [
                for (final d in await api.adminDepartmentFunds(_adminRegionId!))
                  if (d.fund != null) d.fund!,
              ];
      } else {
        funds = await api.myFunds();
      }
      final depts =
          [
            for (final f in funds)
              if (f.ownerType == 'department') f,
          ]..sort((a, b) {
            final ai = kAdminRegionOrder.indexOf((a.regionCode ?? '').toUpperCase());
            final bi = kAdminRegionOrder.indexOf((b.regionCode ?? '').toUpperCase());
            return (ai < 0 ? 99 : ai).compareTo(bi < 0 ? 99 : bi);
          });
      final picked = _defaultFund(depts);
      if (!mounted) return;
      setState(() {
        _funds = depts;
        _fundId = picked?.id;
      });
      // Keep the full-screen loader up until the bills are in too, so the form doesn't
      // appear half-empty and then fill in.
      if (_fundId != null) await _loadBills(_fundId!);
      if (mounted) setState(() => _loading = false);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  Future<void> _loadBills(int fundId) async {
    setState(() {
      _loadingBills = true;
      _error = null;
      _selected.clear();
      _bills = const [];
    });
    try {
      final bills = await ref.read(apiClientProvider).replenishableBills(fundId);
      if (!mounted) return;
      setState(() {
        _bills = bills;
        _selected.addAll(bills.map((b) => b.id));
        _loadingBills = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loadingBills = false;
      });
    }
  }

  Future<void> _save() async {
    if (_fundId == null) {
      setState(() => _error = 'Pick a department');
      return;
    }
    if (_selected.isEmpty) {
      setState(() => _error = 'Pick the petty-cash bills to replenish');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref
          .read(apiClientProvider)
          .createTopup(
            _fundId!,
            remarks: _remarks.text.trim().isEmpty ? null : _remarks.text.trim(),
            transactionIds: _selected.toList(),
          );
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final fund = _funds.cast<PettyCashFund?>().firstWhere((f) => f?.id == _fundId, orElse: () => null);
    final currency = fund?.currency ?? '';
    final lockDepartment = widget.fundId != null || _funds.length <= 1;
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: const BrandAppBar(title: 'Request top-up', automaticallyImplyLeading: true, showMenuAction: false),
      // Nothing to fill in until the department and its bills are known: show a loader and
      // shimmering bill rows instead of an empty form.
      body: _loading
          ? const _RaiseTopupLoading()
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                if (_regions.length > 1) ...[
                  Wrap(
                    spacing: 8,
                    runSpacing: 6,
                    children: [
                      for (final r in _regions)
                        ChoiceChip(
                          label: Text(companyLabel(r.regionCode)),
                          selected: r.id == _adminRegionId,
                          onSelected: _loading
                              ? null
                              : (_) {
                                  if (r.id == _adminRegionId) return;
                                  setState(() {
                                    _adminRegionId = r.id;
                                    _fundId = null;
                                  });
                                  _load();
                                },
                        ),
                    ],
                  ),
                  const SizedBox(height: 16),
                ],
                if (_funds.isEmpty && !_loading)
                  const Text(
                    'No department pot is set up for you yet. Ask Admin to set an approved limit.',
                    style: TextStyle(color: AppColors.textSecondary, height: 1.35),
                  )
                else if (lockDepartment)
                  InputDecorator(
                    decoration: const InputDecoration(labelText: 'Department'),
                    child: Text(
                      fund != null ? _fundLabel(fund) : 'Your department',
                      style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                    ),
                  )
                else
                  DropdownButtonFormField<int>(
                    key: ValueKey(_fundId),
                    isExpanded: true,
                    initialValue: _fundId,
                    decoration: const InputDecoration(labelText: 'Department'),
                    items: [
                      for (final f in _funds)
                        DropdownMenuItem(
                          value: f.id,
                          child: Text(_fundLabel(f), overflow: TextOverflow.ellipsis),
                        ),
                    ],
                    onChanged: (v) {
                      setState(() => _fundId = v);
                      if (v != null) _loadBills(v);
                    },
                  ),
                const SizedBox(height: 16),
                Text(
                  'Amount  ${formatMoney(currency, _amount)}',
                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
                ),
                const SizedBox(height: 12),
                if (_loadingBills)
                  // Switching department: shimmer just the bill list, keep the rest of the form.
                  const _BillRowsShimmer()
                else if (_bills.isEmpty)
                  const Text(
                    'No unreplenished petty-cash bills for this department.',
                    style: TextStyle(color: AppColors.textSecondary),
                  )
                else ...[
                  for (final bill in _bills)
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      value: _selected.contains(bill.id),
                      onChanged: (on) {
                        setState(() {
                          if (on == true) {
                            _selected.add(bill.id);
                          } else {
                            _selected.remove(bill.id);
                          }
                        });
                      },
                      title: Text(formatMoney(bill.currency ?? currency, bill.amount)),
                      subtitle: Text(
                        [
                          if (bill.billDate != null && bill.billDate!.isNotEmpty) bill.billDate,
                          '#${bill.id}',
                          if (bill.isPartOfBill)
                            'your department\'s part of ${formatMoney(bill.currency ?? currency, bill.billTotal!)}',
                        ].whereType<String>().join(' · '),
                      ),
                    ),
                ],
                const SizedBox(height: 12),
                TextField(
                  controller: _remarks,
                  decoration: const InputDecoration(labelText: 'Reason (optional)'),
                ),
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: _busy || _loadingBills ? null : _save,
                  child: Text(_busy ? 'Sending…' : 'Submit request'),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 8),
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                ],
              ],
            ),
    );
  }
}

/// Full-screen loading state for Request top-up: a large spinner plus shimmering bill rows
/// (no empty input fields while there's nothing to fill in yet).
class _RaiseTopupLoading extends StatelessWidget {
  const _RaiseTopupLoading();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 40, 20, 20),
      children: const [
        Center(child: SizedBox(width: 48, height: 48, child: CircularProgressIndicator(strokeWidth: 4))),
        SizedBox(height: 16),
        Center(
          child: Text(
            'Loading petty-cash bills…',
            style: TextStyle(color: AppColors.textSecondary, fontSize: 15, fontWeight: FontWeight.w600),
          ),
        ),
        SizedBox(height: 32),
        ShimmerBox(height: 14, widthFraction: 0.45),
        SizedBox(height: 20),
        _BillRowsShimmer(),
      ],
    );
  }
}

/// Placeholder for the bill list: a tick + amount + detail line per row.
class _BillRowsShimmer extends StatelessWidget {
  const _BillRowsShimmer();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        for (var i = 0; i < 4; i++)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 10),
            child: Row(
              children: [
                ShimmerBox(height: 20, width: 20, borderRadius: BorderRadius.all(Radius.circular(4))),
                SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      ShimmerBox(height: 14, widthFraction: 0.35),
                      SizedBox(height: 8),
                      ShimmerBox(height: 11, widthFraction: 0.6),
                    ],
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}

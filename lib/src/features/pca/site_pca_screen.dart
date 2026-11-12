// Employee petty cash for Blue Rhine Contracting (companies with pca_model "site").
//
// No HODs. Each employee holds one petty cash for all their sites, set by the Accountant. Every
// bill names its site's OP code; petty-cash bills come off the employee's petty cash.
// Top-up: the Accountant prepares it from approved bills -> the Head of Accountant approves ->
// the Finance Manager approves and records the cash withdrawal from the bank -> the petty cash
// is back to its limit. Backend: /api/site-pca (services/site_pca_service.py).
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../api/enums.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/money.dart';
import '../../widgets/app_nav_drawer.dart';
import '../../widgets/brand_app_bar.dart';
import '../admin/my_funds_screen.dart';
import '../authentication/auth_controller.dart';

/// The site-pot company this screen shows: the one the user is signed in under, else (Admin)
/// the first company on the site model.
final sitePcaRegionProvider = FutureProvider.autoDispose<RegionConfig?>((ref) async {
  final user = ref.watch(authControllerProvider).user;
  final regions = await ref.watch(apiClientProvider).listRegions();
  final sites = [for (final r in regions) if (r.usesSitePots) r];
  final code = (user?.regionCode ?? '').toUpperCase();
  for (final r in sites) {
    if (r.regionCode.toUpperCase() == code) return r;
  }
  return sites.isEmpty ? null : sites.first;
});

final sitePotsProvider = FutureProvider.autoDispose.family<List<PettyCashFund>, int>((ref, regionId) {
  return ref.watch(apiClientProvider).sitePots(regionId: regionId);
});

final siteTopupsProvider = FutureProvider.autoDispose.family<List<TopupRequest>, int>((ref, regionId) {
  return ref.watch(apiClientProvider).siteRequests(regionId: regionId, kind: 'topup');
});

void _refreshAll(WidgetRef ref, int regionId) {
  ref.invalidate(sitePotsProvider(regionId));
  ref.invalidate(siteTopupsProvider(regionId));
  ref.invalidate(myFundsProvider);
}

String _errorText(Object e) {
  final text = '$e';
  final match = RegExp(r'"detail"\s*:\s*"([^"]+)"').firstMatch(text);
  return match?.group(1) ?? text.replaceFirst('Exception: ', '');
}

String _ymd(DateTime d) => DateFormat('yyyy-MM-dd').format(d);

class SitePcaScreen extends ConsumerWidget {
  const SitePcaScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    final role = UserRoleX.fromJson(user?.role);
    final regionAsync = ref.watch(sitePcaRegionProvider);
    final isEmployee = role == UserRole.employee;
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        drawer: const AppNavDrawer(),
        appBar: BrandAppBar(title: isEmployee ? 'My petty cash' : 'Petty cash'),
        body: regionAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Center(child: Text(_errorText(e), style: const TextStyle(color: AppColors.danger))),
          data: (region) {
            if (region == null) {
              return const Center(
                child: Padding(
                  padding: EdgeInsets.all(24),
                  child: Text('No company uses this petty cash flow.', textAlign: TextAlign.center),
                ),
              );
            }
            return Column(
              children: [
                Material(
                  color: AppColors.card,
                  child: TabBar(
                    labelColor: AppColors.darkBlue,
                    indicatorColor: AppColors.darkBlue,
                    tabs: [
                      Tab(text: isEmployee ? 'My petty cash' : 'Employees'),
                      const Tab(text: 'Top-ups'),
                    ],
                  ),
                ),
                Expanded(
                  child: TabBarView(
                    children: [
                      _PotsTab(region: region, role: role),
                      _TopupsTab(region: region, role: role),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

// ---- pots ----------------------------------------------------------------------------------

class _PotsTab extends ConsumerWidget {
  const _PotsTab({required this.region, required this.role});

  final RegionConfig region;
  final UserRole role;

  bool get _canSet => role == UserRole.accountant || role == UserRole.admin;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(sitePotsProvider(region.id));
    return Scaffold(
      backgroundColor: AppColors.background,
      floatingActionButton: _canSet
          ? FloatingActionButton.extended(
              heroTag: 'site-pca-set',
              onPressed: () => _openSetSheet(context, ref, region),
              icon: Icon(PhosphorIcons.plus()),
              label: const Text('Set petty cash'),
            )
          : null,
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(sitePotsProvider(region.id).future),
        child: async.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => ListView(
            padding: const EdgeInsets.all(24),
            children: [Text(_errorText(e), style: const TextStyle(color: AppColors.danger))],
          ),
          data: (pots) {
            if (pots.isEmpty) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  Text(
                    _canSet
                        ? 'No petty cash yet. Tap "Set petty cash" to give an employee petty cash.'
                        : role == UserRole.employee
                            ? 'You have no petty cash yet. The Accountant sets it. Until then, '
                                'submit bills as reimbursements.'
                            : 'No petty cash yet.',
                    style: const TextStyle(color: AppColors.textSecondary, height: 1.4),
                  ),
                ],
              );
            }
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
              children: [
                for (final pot in pots)
                  _PotCard(
                    pot: pot,
                    canSet: _canSet,
                    onChange: () => _openSetSheet(context, ref, region, pot: pot),
                    onTopup: () => _openTopupSheet(context, ref, region, pot),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }
}

Future<void> _openSetSheet(BuildContext context, WidgetRef ref, RegionConfig region, {PettyCashFund? pot}) async {
  final done = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    builder: (_) => _SetPotSheet(region: region, pot: pot),
  );
  if (done == true) _refreshAll(ref, region.id);
}

Future<void> _openTopupSheet(BuildContext context, WidgetRef ref, RegionConfig region, PettyCashFund pot) async {
  final done = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    builder: (_) => _PrepareTopupSheet(pot: pot),
  );
  if (done == true) {
    _refreshAll(ref, region.id);
    if (context.mounted) DefaultTabController.of(context).animateTo(1);
  }
}

class _PotCard extends StatelessWidget {
  const _PotCard({required this.pot, required this.canSet, required this.onChange, required this.onTopup});

  final PettyCashFund pot;
  final bool canSet;
  final VoidCallback onChange;
  final VoidCallback onTopup;

  @override
  Widget build(BuildContext context) {
    final limit = pot.approvedLimit;
    final left = pot.available;
    final share = limit > 0 ? (left / limit).clamp(0.0, 1.0) : 0.0;
    final barColor = share < 0.2 ? AppColors.danger : (share < 0.5 ? AppColors.orange : AppColors.success);
    final toTopUp = (pot.spent - pot.credited).clamp(0.0, double.infinity) - pot.pendingTopup;
    const secondary = TextStyle(color: AppColors.textSecondary, fontSize: 12.5);
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                PhosphorIcon(PhosphorIcons.user(), size: 18, color: AppColors.darkBlue),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    pot.employeeName ?? 'Employee',
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text('${formatMoney(pot.currency, left)} left',
                style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 20, color: AppColors.darkBlue)),
            Text('of ${formatMoney(pot.currency, limit)}', style: secondary),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: share,
                minHeight: 7,
                color: barColor,
                backgroundColor: AppColors.divider,
              ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 14,
              runSpacing: 4,
              children: [
                Text('Spent ${formatMoney(pot.currency, pot.spent)}', style: secondary),
                if (pot.pendingBills > 0) Text('In approval ${formatMoney(pot.currency, pot.pendingBills)}', style: secondary),
                if (pot.pendingTopup > 0) Text('Top-up in progress ${formatMoney(pot.currency, pot.pendingTopup)}', style: secondary),
              ],
            ),
            if (canSet)
              Row(
                children: [
                  TextButton.icon(
                    onPressed: onChange,
                    icon: Icon(PhosphorIcons.pencilSimple(), size: 16),
                    label: const Text('Change amount'),
                  ),
                  const Spacer(),
                  if (toTopUp > 0.004)
                    FilledButton.icon(
                      onPressed: onTopup,
                      icon: Icon(PhosphorIcons.arrowCounterClockwise(), size: 16),
                      label: Text('Prepare top-up · ${formatMoney(pot.currency, toTopUp)}'),
                    ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

class _SetPotSheet extends ConsumerStatefulWidget {
  const _SetPotSheet({required this.region, this.pot});

  final RegionConfig region;
  final PettyCashFund? pot;

  @override
  ConsumerState<_SetPotSheet> createState() => _SetPotSheetState();
}

class _SetPotSheetState extends ConsumerState<_SetPotSheet> {
  late final _amount = TextEditingController(
    text: widget.pot == null ? '' : widget.pot!.approvedLimit.toStringAsFixed(2),
  );
  final _remarks = TextEditingController();
  List<PcaStaff>? _people;
  int? _employeeId;
  bool _busy = false;
  String? _error;

  bool get _editing => widget.pot != null;

  @override
  void initState() {
    super.initState();
    _employeeId = widget.pot?.employeeId;
    if (!_editing) _loadPeople();
  }

  Future<void> _loadPeople() async {
    try {
      final people = await ref.read(apiClientProvider).sitePeople(widget.region.id);
      if (mounted) setState(() => _people = people);
    } catch (e) {
      if (mounted) setState(() => _error = _errorText(e));
    }
  }

  @override
  void dispose() {
    _amount.dispose();
    _remarks.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final employeeId = _employeeId;
    final amount = double.tryParse(_amount.text.replaceAll(',', '').trim());
    if (employeeId == null) {
      setState(() => _error = 'Pick the employee');
      return;
    }
    if (amount == null || amount < 0) {
      setState(() => _error = 'Enter the amount');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).setSitePot(
            regionId: widget.region.id,
            employeeId: employeeId,
            amount: amount,
            remarks: _remarks.text.trim().isEmpty ? null : _remarks.text.trim(),
          );
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) setState(() => _error = _errorText(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final currency = widget.region.baseCurrency ?? widget.pot?.currency ?? 'AED';
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 20, 20, 20 + MediaQuery.viewInsetsOf(context).bottom),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(_editing ? 'Change petty cash' : 'Set petty cash', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 4),
            const Text(
              'Live at once, for all the employee\'s sites. Their petty-cash bills come off it; '
              'a top-up brings it back to this amount.',
              style: TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 16),
            if (_editing)
              InputDecorator(
                decoration: const InputDecoration(labelText: 'Employee'),
                child: Text(widget.pot!.employeeName ?? ''),
              )
            else if (_people == null)
              const Padding(padding: EdgeInsets.all(12), child: Center(child: CircularProgressIndicator()))
            else
              DropdownButtonFormField<int>(
                initialValue: _employeeId,
                isExpanded: true,
                decoration: const InputDecoration(labelText: 'Employee *'),
                items: [
                  for (final p in _people!)
                    DropdownMenuItem(
                      value: p.id,
                      child: Text(
                        [
                          p.displayName,
                          if (p.departmentName != null) p.departmentName!,
                          if (p.advance > 0) formatMoney(currency, p.advance),
                        ].join(' · '),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                ],
                onChanged: _busy
                    ? null
                    : (v) => setState(() {
                          _employeeId = v;
                          // Someone who already has petty cash: start from their amount.
                          final current = _people!.where((p) => p.id == v).firstOrNull?.advance ?? 0;
                          if (current > 0) _amount.text = current.toStringAsFixed(2);
                        }),
              ),
            const SizedBox(height: 12),
            TextField(
              controller: _amount,
              enabled: !_busy,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(labelText: 'Amount ($currency) *'),
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
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: _busy ? null : _save,
              style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(48)),
              icon: Icon(PhosphorIcons.checkCircle(), size: 20),
              label: const Text('Save'),
            ),
          ],
        ),
      ),
    );
  }
}

class _PrepareTopupSheet extends ConsumerStatefulWidget {
  const _PrepareTopupSheet({required this.pot});

  final PettyCashFund pot;

  @override
  ConsumerState<_PrepareTopupSheet> createState() => _PrepareTopupSheetState();
}

class _PrepareTopupSheetState extends ConsumerState<_PrepareTopupSheet> {
  List<ReplenishableBill>? _bills;
  final Set<int> _picked = {};
  final _remarks = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final bills = await ref.read(apiClientProvider).siteReplenishableBills(widget.pot.id);
      if (mounted) {
        setState(() {
          _bills = bills;
          _picked.addAll(bills.map((b) => b.id));
        });
      }
    } catch (e) {
      if (mounted) setState(() => _error = _errorText(e));
    }
  }

  @override
  void dispose() {
    _remarks.dispose();
    super.dispose();
  }

  double get _total => (_bills ?? const <ReplenishableBill>[])
      .where((b) => _picked.contains(b.id))
      .fold(0.0, (sum, b) => sum + b.amount);

  Future<void> _save() async {
    if (_picked.isEmpty) {
      setState(() => _error = 'Pick the approved bills to top up');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).siteRequestTopup(
            widget.pot.id,
            transactionIds: _picked.toList(),
            remarks: _remarks.text.trim().isEmpty ? null : _remarks.text.trim(),
          );
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) setState(() => _error = _errorText(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final pot = widget.pot;
    final bills = _bills;
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 20, 20, 20 + MediaQuery.viewInsetsOf(context).bottom),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Prepare top-up', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(pot.employeeName ?? '', style: const TextStyle(color: AppColors.textSecondary)),
            const SizedBox(height: 12),
            if (bills == null && _error == null)
              const Padding(padding: EdgeInsets.all(16), child: Center(child: CircularProgressIndicator()))
            else if (bills != null && bills.isEmpty)
              const Text('No approved bills left to top up.')
            else if (bills != null)
              for (final b in bills)
                CheckboxListTile(
                  contentPadding: EdgeInsets.zero,
                  value: _picked.contains(b.id),
                  onChanged: _busy
                      ? null
                      : (v) => setState(() => v == true ? _picked.add(b.id) : _picked.remove(b.id)),
                  title: Text('Bill #${b.id} · ${formatMoney(b.currency ?? pot.currency, b.amount)}'),
                  subtitle: Text([
                    if (b.billDate != null) b.billDate!,
                    if (b.isPartOfBill) 'part of ${formatMoney(b.currency ?? pot.currency, b.billTotal!)}',
                  ].join(' · ')),
                ),
            const SizedBox(height: 8),
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
              onPressed: _busy || _picked.isEmpty ? null : _save,
              style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(48)),
              icon: Icon(PhosphorIcons.paperPlaneTilt(), size: 20),
              label: Text('Send to Head of Accountant · ${formatMoney(pot.currency, _total)}'),
            ),
          ],
        ),
      ),
    );
  }
}

// ---- top-ups -------------------------------------------------------------------------------

const _statusLabels = {
  'submitted': 'With Head of Accountant',
  'verified': 'With Finance Manager',
  'paid': 'Paid · pot refilled',
  'rejected': 'Rejected',
};

class _TopupsTab extends ConsumerWidget {
  const _TopupsTab({required this.region, required this.role});

  final RegionConfig region;
  final UserRole role;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(siteTopupsProvider(region.id));
    return RefreshIndicator(
      onRefresh: () => ref.refresh(siteTopupsProvider(region.id).future),
      child: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => ListView(
          padding: const EdgeInsets.all(24),
          children: [Text(_errorText(e), style: const TextStyle(color: AppColors.danger))],
        ),
        data: (rows) {
          if (rows.isEmpty) {
            return ListView(
              padding: const EdgeInsets.all(24),
              children: const [
                Text('No top-ups yet. The Accountant prepares one from an employee\'s approved bills.',
                    style: TextStyle(color: AppColors.textSecondary, height: 1.4)),
              ],
            );
          }
          // Waiting on this user first.
          bool mine(TopupRequest r) => _actionsFor(r, role).isNotEmpty;
          final sorted = [...rows.where(mine), ...rows.where((r) => !mine(r))];
          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [for (final r in sorted) _TopupCard(request: r, role: role, regionId: region.id)],
          );
        },
      ),
    );
  }
}

enum _Action { approve, pay, reject }

List<_Action> _actionsFor(TopupRequest r, UserRole role) {
  final admin = role == UserRole.admin;
  if (r.status == 'submitted' && (role == UserRole.headAccountant || admin)) {
    return const [_Action.approve, _Action.reject];
  }
  if (r.status == 'verified' && (role == UserRole.financeManager || admin)) {
    return const [_Action.pay, _Action.reject];
  }
  return const [];
}

class _TopupCard extends ConsumerWidget {
  const _TopupCard({required this.request, required this.role, required this.regionId});

  final TopupRequest request;
  final UserRole role;
  final int regionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final r = request;
    final currency = r.fund?.currency ?? 'AED';
    final actions = _actionsFor(r, role);
    final statusColor = switch (r.status) {
      'paid' => AppColors.success,
      'rejected' => AppColors.danger,
      _ => AppColors.orange,
    };
    const secondary = TextStyle(color: AppColors.textSecondary, fontSize: 12.5);
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(formatMoney(currency, r.amount),
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18, color: AppColors.darkBlue)),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(_statusLabels[r.status] ?? r.status,
                      style: TextStyle(color: statusColor, fontWeight: FontWeight.w700, fontSize: 12)),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(r.employeeName ?? '', style: const TextStyle(fontWeight: FontWeight.w600)),
            Text('${r.transactionIds.length} bill(s) · prepared by ${r.requesterName ?? '—'}', style: secondary),
            if (r.paymentReference != null) Text('Bank ref ${r.paymentReference}', style: secondary),
            if ((r.remarks ?? '').isNotEmpty) Text('"${r.remarks}"', style: secondary),
            if (r.history.isNotEmpty) ...[
              const SizedBox(height: 6),
              for (final h in r.history)
                Text(
                  '• ${h.action}${h.actorName == null ? '' : ' by ${h.actorName}'}'
                  '${h.at == null ? '' : ' · ${DateFormat('d MMM').format(h.at!.toLocal())}'}'
                  '${(h.comment ?? '').isEmpty ? '' : ' · ${h.comment}'}',
                  style: secondary,
                ),
            ],
            if (actions.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Row(
                  children: [
                    if (actions.contains(_Action.reject))
                      TextButton(
                        onPressed: () => _reject(context, ref),
                        style: TextButton.styleFrom(foregroundColor: AppColors.danger),
                        child: const Text('Reject'),
                      ),
                    const Spacer(),
                    if (actions.contains(_Action.approve))
                      FilledButton(onPressed: () => _approve(context, ref), child: const Text('Approve')),
                    if (actions.contains(_Action.pay))
                      FilledButton(
                        onPressed: () => _pay(context, ref),
                        style: FilledButton.styleFrom(backgroundColor: AppColors.success),
                        child: const Text('Approve & record payment'),
                      ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _run(BuildContext context, WidgetRef ref, Future<void> Function() call, String done) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      await call();
      _refreshAll(ref, regionId);
      messenger.showSnackBar(SnackBar(content: Text(done)));
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(_errorText(e)), backgroundColor: AppColors.danger));
    }
  }

  Future<void> _approve(BuildContext context, WidgetRef ref) async {
    final remarks = await _askText(context, title: 'Approve top-up', label: 'Comment (optional)', required: false);
    if (remarks == null || !context.mounted) return;
    await _run(context, ref, () => ref.read(apiClientProvider).siteApprove(request.id, remarks: remarks.isEmpty ? null : remarks),
        'Approved. Sent to the Finance Manager.');
  }

  Future<void> _reject(BuildContext context, WidgetRef ref) async {
    final comment = await _askText(context, title: 'Reject top-up', label: 'Reason *', required: true);
    if (comment == null || !context.mounted) return;
    await _run(context, ref, () => ref.read(apiClientProvider).siteReject(request.id, comment: comment), 'Rejected.');
  }

  Future<void> _pay(BuildContext context, WidgetRef ref) async {
    final done = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (_) => _PaySheet(request: request),
    );
    if (done == true) _refreshAll(ref, regionId);
  }
}

Future<String?> _askText(BuildContext context, {required String title, required String label, required bool required}) {
  final controller = TextEditingController();
  return showDialog<String>(
    context: context,
    builder: (ctx) => StatefulBuilder(
      builder: (ctx, setState) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: InputDecoration(labelText: label),
          onChanged: (_) => setState(() {}),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Cancel')),
          FilledButton(
            onPressed: required && controller.text.trim().isEmpty
                ? null
                : () => Navigator.of(ctx).pop(controller.text.trim()),
            child: const Text('OK'),
          ),
        ],
      ),
    ),
  );
}

class _PaySheet extends ConsumerStatefulWidget {
  const _PaySheet({required this.request});

  final TopupRequest request;

  @override
  ConsumerState<_PaySheet> createState() => _PaySheetState();
}

class _PaySheetState extends ConsumerState<_PaySheet> {
  final _reference = TextEditingController();
  final _remarks = TextEditingController();
  String _method = 'bank_transfer';
  DateTime _date = DateUtils.dateOnly(DateTime.now());
  bool _busy = false;
  String? _error;

  static const _methods = {
    'bank_transfer': 'Bank transfer',
    'cash': 'Cash withdrawal',
    'cheque': 'Cheque',
  };

  @override
  void dispose() {
    _reference.dispose();
    _remarks.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final reference = _reference.text.trim();
    if (reference.isEmpty) {
      setState(() => _error = 'Enter the bank withdrawal reference');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).sitePay(
            widget.request.id,
            method: _method,
            reference: reference,
            paymentDate: _ymd(_date),
            remarks: _remarks.text.trim().isEmpty ? null : _remarks.text.trim(),
          );
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) setState(() => _error = _errorText(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final r = widget.request;
    final currency = r.fund?.currency ?? 'AED';
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 20, 20, 20 + MediaQuery.viewInsetsOf(context).bottom),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Approve & record payment', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(
              '${formatMoney(currency, r.amount)} for ${r.employeeName ?? ''}. '
              'Recording the cash withdrawal from the bank refills the petty cash.',
              style: const TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: _method,
              decoration: const InputDecoration(labelText: 'Method'),
              items: [
                for (final e in _methods.entries) DropdownMenuItem(value: e.key, child: Text(e.value)),
              ],
              onChanged: _busy ? null : (v) => setState(() => _method = v ?? _method),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _reference,
              enabled: !_busy,
              decoration: const InputDecoration(labelText: 'Bank reference *', hintText: 'Withdrawal or transfer number'),
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
              style: FilledButton.styleFrom(backgroundColor: AppColors.success, minimumSize: const Size.fromHeight(48)),
              icon: Icon(PhosphorIcons.checkCircle(), size: 20),
              label: const Text('Approve & record payment'),
            ),
          ],
        ),
      ),
    );
  }
}

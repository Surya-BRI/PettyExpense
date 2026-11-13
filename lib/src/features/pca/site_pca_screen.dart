// Employee petty cash for Blue Rhine Contracting (companies with pca_model "site").
//
// No HODs. Each employee holds one petty cash for all their sites, set by the Accountant. Every
// bill names its site's OP code; petty-cash bills come off the employee's petty cash.
// Top-up: the Accountant prepares it from approved bills -> the Head of Accountant approves ->
// the Finance Manager approves and records the cash withdrawal from the bank -> the petty cash
// is back to its limit. Backend: /api/site-pca (services/site_pca_service.py).
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
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
import '../shared/status_chip.dart';

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

/// The company's people (Accounts / Admin): the Employees list, with or without petty cash.
final sitePeopleProvider = FutureProvider.autoDispose.family<List<PcaStaff>, int>((ref, regionId) {
  return ref.watch(apiClientProvider).sitePeople(regionId);
});

/// Petty cash amount changes ("set"), for an employee's history.
final siteSetsProvider = FutureProvider.autoDispose.family<List<TopupRequest>, int>((ref, regionId) {
  return ref.watch(apiClientProvider).siteRequests(regionId: regionId, kind: 'advance');
});

/// One employee's bills in the company: (regionId, employeeId).
final siteEmployeeBillsProvider =
    FutureProvider.autoDispose.family<List<ExpenseClaim>, (int, int)>((ref, key) {
  return ref.watch(apiClientProvider).siteEmployeeBills(regionId: key.$1, employeeId: key.$2);
});

void _refreshAll(WidgetRef ref, int regionId) {
  ref.invalidate(sitePotsProvider(regionId));
  ref.invalidate(siteTopupsProvider(regionId));
  ref.invalidate(sitePeopleProvider(regionId));
  ref.invalidate(siteSetsProvider(regionId));
  ref.invalidate(siteEmployeeBillsProvider);
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
    if (isEmployee && user != null) {
      // An employee's own petty cash: the same page Accounts open for them, in "you" words.
      return regionAsync.when(
        loading: () => Scaffold(
          drawer: const AppNavDrawer(),
          appBar: const BrandAppBar(title: 'My petty cash'),
          body: const Center(child: CircularProgressIndicator()),
        ),
        error: (e, _) => Scaffold(
          drawer: const AppNavDrawer(),
          appBar: const BrandAppBar(title: 'My petty cash'),
          body: Center(child: Text(_errorText(e), style: const TextStyle(color: AppColors.danger))),
        ),
        data: (region) => region == null
            ? const Scaffold(
                drawer: AppNavDrawer(),
                appBar: BrandAppBar(title: 'My petty cash'),
                body: Center(child: Text('No company uses this petty cash flow.')),
              )
            : SiteEmployeeScreen(
                region: region,
                role: role,
                own: true,
                person: PcaStaff(id: user.id, displayName: user.displayName, departmentName: user.departmentName),
              ),
      );
    }
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
                      SitePotsView(region: region, role: role),
                      SiteTopupsView(region: region, role: role),
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

/// Each employee's petty cash in one site-model company, with "Set petty cash" for the
/// Accountant / Admin. Also Admin's Company screen tab for that company.
class SitePotsView extends ConsumerWidget {
  const SitePotsView({super.key, required this.region, required this.role});

  final RegionConfig region;
  final UserRole role;

  /// Sets / changes petty cash: Accountant, Head of Accountant, Admin.
  bool get _canSet => role == UserRole.accountant || role == UserRole.headAccountant || role == UserRole.admin;

  /// Accounts at every level and Admin see everyone in the company; an employee their own.
  bool get _seesEveryone =>
      _canSet || role == UserRole.headAccountant || role == UserRole.financeManager;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (_seesEveryone) return _EmployeesList(region: region, role: role, canSet: _canSet);
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

Future<void> _openSetSheet(
  BuildContext context,
  WidgetRef ref,
  RegionConfig region, {
  PettyCashFund? pot,
  PcaStaff? employee,
}) async {
  final done = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    builder: (_) => _SetPotSheet(region: region, pot: pot, employee: employee),
  );
  if (done == true) _refreshAll(ref, region.id);
}

// ---- employees list (Accounts / Admin) -----------------------------------------------------

/// Everyone in the company: their petty cash left of its amount, or "Not set". Tap one for
/// their petty cash, bills, top-ups and changes.
class _EmployeesList extends ConsumerStatefulWidget {
  const _EmployeesList({required this.region, required this.role, required this.canSet});

  final RegionConfig region;
  final UserRole role;
  final bool canSet;

  @override
  ConsumerState<_EmployeesList> createState() => _EmployeesListState();
}

class _EmployeesListState extends ConsumerState<_EmployeesList> {
  final _search = TextEditingController();

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _refresh() async {
    _refreshAll(ref, widget.region.id);
    await ref.read(sitePeopleProvider(widget.region.id).future);
  }

  @override
  Widget build(BuildContext context) {
    final region = widget.region;
    final peopleAsync = ref.watch(sitePeopleProvider(region.id));
    final potsAsync = ref.watch(sitePotsProvider(region.id));
    return Scaffold(
      backgroundColor: AppColors.background,
      floatingActionButton: widget.canSet
          ? FloatingActionButton.extended(
              heroTag: 'site-pca-set',
              onPressed: () => _openSetSheet(context, ref, region),
              icon: Icon(PhosphorIcons.plus()),
              label: const Text('Set petty cash'),
            )
          : null,
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: Builder(
          builder: (context) {
            final error = peopleAsync.error ?? potsAsync.error;
            if (error != null) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: [Text(_errorText(error), style: const TextStyle(color: AppColors.danger))],
              );
            }
            final people = peopleAsync.valueOrNull;
            final pots = potsAsync.valueOrNull;
            if (people == null || pots == null) return const Center(child: CircularProgressIndicator());
            final potBy = {for (final p in pots) if (p.employeeId != null) p.employeeId!: p};
            // Everyone in the company, plus anyone holding petty cash here who isn't any more.
            final rows = [
              ...people,
              for (final p in pots)
                if (p.employeeId != null && !people.any((x) => x.id == p.employeeId))
                  PcaStaff(id: p.employeeId!, displayName: p.employeeName ?? 'Employee', advance: p.approvedLimit),
            ];
            final q = _search.text.trim().toLowerCase();
            final shown = [
              for (final r in rows)
                if (q.isEmpty ||
                    r.displayName.toLowerCase().contains(q) ||
                    (r.departmentName ?? '').toLowerCase().contains(q))
                  r,
            ];
            final withCash = rows.where((r) => potBy.containsKey(r.id)).length;
            if (rows.isEmpty) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: const [
                  Text(
                    'Nobody belongs to this company yet. In People, set their company or tick it for them.',
                    style: TextStyle(color: AppColors.textSecondary, height: 1.4),
                  ),
                ],
              );
            }
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 96),
              children: [
                TextField(
                  controller: _search,
                  onChanged: (_) => setState(() {}),
                  decoration: InputDecoration(
                    hintText: 'Search name or department',
                    prefixIcon: Icon(PhosphorIcons.magnifyingGlass(), size: 18),
                    isDense: true,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  '${rows.length} employees · $withCash with petty cash · ${rows.length - withCash} not set',
                  style: const TextStyle(color: AppColors.textSecondary, fontSize: 12.5),
                ),
                const SizedBox(height: 8),
                for (final person in shown)
                  _EmployeeRow(
                    person: person,
                    pot: potBy[person.id],
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => SiteEmployeeScreen(region: region, person: person, role: widget.role),
                      ),
                    ),
                  ),
                if (shown.isEmpty)
                  const Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('No one matches.', style: TextStyle(color: AppColors.textSecondary)),
                  ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _EmployeeRow extends StatelessWidget {
  const _EmployeeRow({required this.person, required this.pot, required this.onTap});

  final PcaStaff person;
  final PettyCashFund? pot;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final pot = this.pot;
    const secondary = TextStyle(color: AppColors.textSecondary, fontSize: 12.5);
    final initials = person.displayName.trim().isEmpty ? '?' : person.displayName.trim()[0].toUpperCase();
    Widget trailing;
    if (pot == null) {
      trailing = Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(color: AppColors.divider, borderRadius: BorderRadius.circular(20)),
        child: const Text('Not set', style: TextStyle(color: AppColors.textSecondary, fontWeight: FontWeight.w600, fontSize: 12)),
      );
    } else {
      final share = pot.approvedLimit > 0 ? (pot.available / pot.approvedLimit).clamp(0.0, 1.0) : 0.0;
      final color = share < 0.2 ? AppColors.danger : (share < 0.5 ? AppColors.orange : AppColors.success);
      trailing = SizedBox(
        width: 120,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(formatMoney(pot.currency, pot.available),
                style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.darkBlue)),
            Text('of ${formatMoney(pot.currency, pot.approvedLimit)}', style: secondary),
            const SizedBox(height: 4),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(value: share, minHeight: 4, color: color, backgroundColor: AppColors.divider),
            ),
          ],
        ),
      );
    }
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
          child: Row(
            children: [
              CircleAvatar(
                radius: 18,
                backgroundColor: AppColors.lightBlue,
                child: Text(initials, style: const TextStyle(color: AppColors.darkBlue, fontWeight: FontWeight.w700)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(person.displayName,
                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15), overflow: TextOverflow.ellipsis),
                    if ((person.departmentName ?? '').isNotEmpty)
                      Text(person.departmentName!, style: secondary, overflow: TextOverflow.ellipsis),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              trailing,
              const SizedBox(width: 4),
              Icon(PhosphorIcons.caretRight(), size: 14, color: AppColors.textSecondary),
            ],
          ),
        ),
      ),
    );
  }
}

// ---- one employee --------------------------------------------------------------------------

/// One employee's petty cash: who they are, their petty cash (set / change it, prepare a
/// top-up), their bills, their top-ups and every change to the amount.
class SiteEmployeeScreen extends ConsumerWidget {
  const SiteEmployeeScreen({
    super.key,
    required this.region,
    required this.person,
    required this.role,
    this.own = false,
  });

  final RegionConfig region;
  final PcaStaff person;
  final UserRole role;

  /// The employee's own page ("My petty cash"): menu instead of back, "you" wording.
  final bool own;

  /// Sets / changes petty cash: Accountant, Head of Accountant, Admin.
  bool get _canSet => role == UserRole.accountant || role == UserRole.headAccountant || role == UserRole.admin;

  /// Prepares a top-up: Accountant, Admin (the Head of Accountant approves it).
  bool get _canPrepare => role == UserRole.accountant || role == UserRole.admin;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final potsAsync = ref.watch(sitePotsProvider(region.id));
    final billsAsync = ref.watch(siteEmployeeBillsProvider((region.id, person.id)));
    final topupsAsync = ref.watch(siteTopupsProvider(region.id));
    final setsAsync = ref.watch(siteSetsProvider(region.id));
    final pot = potsAsync.valueOrNull?.where((p) => p.employeeId == person.id).firstOrNull;
    final topups = [
      for (final t in topupsAsync.valueOrNull ?? const <TopupRequest>[])
        if ((t.employeeId ?? t.fund?.employeeId) == person.id) t,
    ];
    // Every change to the amount, newest first.
    final changes = [
      for (final s in setsAsync.valueOrNull ?? const <TopupRequest>[])
        if ((s.employeeId ?? s.fund?.employeeId) == person.id) ...s.history,
    ]..sort((a, b) => (b.at ?? DateTime(0)).compareTo(a.at ?? DateTime(0)));
    final bills = billsAsync.valueOrNull;

    return Scaffold(
      backgroundColor: AppColors.background,
      drawer: own ? const AppNavDrawer() : null,
      appBar: own
          ? const BrandAppBar(title: 'My petty cash')
          : const BrandAppBar(title: 'Employee petty cash', automaticallyImplyLeading: true, showMenuAction: false),
      body: RefreshIndicator(
        onRefresh: () async {
          _refreshAll(ref, region.id);
          await ref.read(sitePotsProvider(region.id).future);
        },
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
          children: [
            _ProfileHeader(person: person, region: region),
            const SizedBox(height: 12),
            if (potsAsync.isLoading && pot == null)
              const _Panel(child: Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator())))
            else if (pot != null)
              _PotSummary(
                pot: pot,
                canSet: _canSet,
                canPrepare: _canPrepare,
                onChange: () => _openSetSheet(context, ref, region, pot: pot),
                onTopup: () => _openTopupSheet(context, ref, region, pot),
              )
            else
              _NoPotPanel(
                canSet: _canSet,
                own: own,
                onSet: () => _openSetSheet(context, ref, region, employee: person),
              ),
            const SizedBox(height: 20),
            _SectionTitle(icon: PhosphorIcons.receipt(), title: 'Bills', count: bills?.length),
            billsAsync.when(
              loading: () => const _Panel(
                child: Padding(padding: EdgeInsets.all(20), child: Center(child: CircularProgressIndicator())),
              ),
              error: (e, _) => _Panel(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(_errorText(e), style: const TextStyle(color: AppColors.danger)),
                ),
              ),
              data: (rows) => rows.isEmpty
                  ? _EmptyPanel(
                      icon: PhosphorIcons.receipt(),
                      text: own ? 'You haven\'t submitted any bills yet.' : 'No bills submitted yet.',
                    )
                  : _Panel(
                      child: Column(
                        children: [
                          for (var i = 0; i < rows.length; i++) ...[
                            if (i > 0) const Divider(height: 1, indent: 14, endIndent: 14),
                            _BillRow(bill: rows[i]),
                          ],
                        ],
                      ),
                    ),
            ),
            const SizedBox(height: 20),
            _SectionTitle(
              icon: PhosphorIcons.arrowCounterClockwise(),
              title: 'Top-ups',
              count: topupsAsync.valueOrNull == null ? null : topups.length,
            ),
            if (topupsAsync.isLoading && topupsAsync.valueOrNull == null)
              const _Panel(child: Padding(padding: EdgeInsets.all(20), child: Center(child: CircularProgressIndicator())))
            else if (topups.isEmpty)
              _EmptyPanel(
                icon: PhosphorIcons.arrowCounterClockwise(),
                text: own
                    ? 'No top-ups yet. After your petty-cash bills are approved, Accounts tops your petty cash back up.'
                    : 'No top-ups yet. The Accountant prepares one from approved petty-cash bills.',
              )
            else
              for (final t in topups) _TopupCard(request: t, role: role, regionId: region.id),
            const SizedBox(height: 20),
            _SectionTitle(
              icon: PhosphorIcons.clockCounterClockwise(),
              title: 'Petty cash changes',
              count: setsAsync.valueOrNull == null ? null : changes.length,
            ),
            if (changes.isEmpty)
              _EmptyPanel(icon: PhosphorIcons.clockCounterClockwise(), text: 'No changes to the amount yet.')
            else
              _Panel(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: Column(
                    children: [
                      for (var i = 0; i < changes.length; i++)
                        _ChangeRow(entry: changes[i], last: i == changes.length - 1),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// White rounded panel used by every block on the employee page.
class _Panel extends StatelessWidget {
  const _Panel({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(16),
      clipBehavior: Clip.antiAlias,
      child: child,
    );
  }
}

class _ProfileHeader extends StatelessWidget {
  const _ProfileHeader({required this.person, required this.region});

  final PcaStaff person;
  final RegionConfig region;

  @override
  Widget build(BuildContext context) {
    final name = person.displayName.trim();
    final parts = name.split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    final initials = parts.isEmpty
        ? '?'
        : (parts.length == 1 ? parts.first[0] : '${parts.first[0]}${parts.last[0]}').toUpperCase();
    final company = (region.companyName ?? region.regionName).trim();
    return _Panel(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              radius: 26,
              backgroundColor: AppColors.lightBlue,
              child: Text(initials,
                  style: const TextStyle(color: AppColors.darkBlue, fontWeight: FontWeight.w800, fontSize: 18)),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name.isEmpty ? 'Employee' : name,
                    style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18, height: 1.2),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Wrap(
                    spacing: 6,
                    runSpacing: 4,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      if ((person.departmentName ?? '').isNotEmpty)
                        _Tag(icon: PhosphorIcons.briefcase(), text: person.departmentName!),
                      if (company.isNotEmpty) _Tag(icon: PhosphorIcons.buildings(), text: company),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Tag extends StatelessWidget {
  const _Tag({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(6)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: AppColors.textSecondary),
          const SizedBox(width: 4),
          Flexible(
            child: Text(text,
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 12), overflow: TextOverflow.ellipsis),
          ),
        ],
      ),
    );
  }
}

/// The employee's petty cash: available against the amount, the three running figures, and
/// (Accountant / Admin) change it or prepare a top-up.
class _PotSummary extends StatelessWidget {
  const _PotSummary({
    required this.pot,
    required this.canSet,
    required this.canPrepare,
    required this.onChange,
    required this.onTopup,
  });

  final PettyCashFund pot;
  final bool canSet;
  final bool canPrepare;
  final VoidCallback onChange;
  final VoidCallback onTopup;

  @override
  Widget build(BuildContext context) {
    final limit = pot.approvedLimit;
    final left = pot.available;
    final share = limit > 0 ? (left / limit).clamp(0.0, 1.0) : 0.0;
    final color = share < 0.2 ? AppColors.danger : (share < 0.5 ? AppColors.orange : AppColors.success);
    final toTopUp = (pot.spent - pot.credited).clamp(0.0, double.infinity) - pot.pendingTopup;
    const secondary = TextStyle(color: AppColors.textSecondary, fontSize: 12.5);
    return _Panel(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(PhosphorIcons.wallet(), size: 18, color: AppColors.darkBlue),
                const SizedBox(width: 6),
                const Expanded(
                  child: Text('Petty cash', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.darkBlue)),
                ),
                Text('${(share * 100).round()}% left', style: TextStyle(color: color, fontWeight: FontWeight.w700, fontSize: 12.5)),
              ],
            ),
            const SizedBox(height: 12),
            const Text('Available', style: secondary),
            const SizedBox(height: 2),
            Row(
              crossAxisAlignment: CrossAxisAlignment.baseline,
              textBaseline: TextBaseline.alphabetic,
              children: [
                Flexible(
                  child: Text(
                    formatMoney(pot.currency, left),
                    style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 26, color: AppColors.textPrimary),
                  ),
                ),
                const SizedBox(width: 6),
                Text('of ${formatMoney(pot.currency, limit)}', style: secondary),
              ],
            ),
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(value: share, minHeight: 8, color: color, backgroundColor: AppColors.background),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                _Figure(label: 'Spent', value: formatMoney(pot.currency, pot.spent)),
                _Figure(
                  label: 'In approval',
                  value: formatMoney(pot.currency, pot.pendingBills),
                  highlight: pot.pendingBills > 0,
                ),
                _Figure(
                  label: 'Top-up on way',
                  value: formatMoney(pot.currency, pot.pendingTopup),
                  highlight: pot.pendingTopup > 0,
                ),
              ],
            ),
            if (canSet) ...[
              const Divider(height: 24),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: onChange,
                      icon: Icon(PhosphorIcons.pencilSimple(), size: 16),
                      label: const Text('Change amount'),
                    ),
                  ),
                  if (canPrepare && toTopUp > 0.004) ...[
                    const SizedBox(width: 10),
                    Expanded(
                      child: FilledButton.icon(
                        onPressed: onTopup,
                        icon: Icon(PhosphorIcons.arrowCounterClockwise(), size: 16),
                        label: Text('Top up ${formatMoney(pot.currency, toTopUp)}', overflow: TextOverflow.ellipsis),
                      ),
                    ),
                  ],
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _Figure extends StatelessWidget {
  const _Figure({required this.label, required this.value, this.highlight = false});

  final String label;
  final String value;
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 11.5)),
          const SizedBox(height: 2),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: 13.5,
              color: highlight ? AppColors.orange : AppColors.textPrimary,
            ),
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}

class _NoPotPanel extends StatelessWidget {
  const _NoPotPanel({required this.canSet, required this.onSet, this.own = false});

  final bool canSet;
  final VoidCallback onSet;
  final bool own;

  @override
  Widget build(BuildContext context) {
    return _Panel(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 24, 20, 20),
        child: Column(
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(color: AppColors.orange.withValues(alpha: 0.10), shape: BoxShape.circle),
              child: Icon(PhosphorIcons.wallet(), color: AppColors.orange, size: 26),
            ),
            const SizedBox(height: 12),
            Text(own ? 'You have no petty cash yet' : 'No petty cash yet',
                style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            const SizedBox(height: 4),
            Text(
              own
                  ? 'Accounts sets it for you. Until then, submit your bills as reimbursements.'
                  : canSet
                      ? 'Give them petty cash for all their sites. It is live as soon as you save.'
                      : 'The Accountant sets it. Until then their bills are reimbursements.',
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.textSecondary, fontSize: 13, height: 1.4),
            ),
            if (canSet) ...[
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: onSet,
                  style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(46)),
                  icon: Icon(PhosphorIcons.plus(), size: 16),
                  label: const Text('Set petty cash'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.icon, required this.title, this.count});

  final IconData icon;
  final String title;
  final int? count;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8),
      child: Row(
        children: [
          Icon(icon, size: 16, color: AppColors.darkBlue),
          const SizedBox(width: 6),
          Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: AppColors.darkBlue)),
          if (count != null && count! > 0) ...[
            const SizedBox(width: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 1),
              decoration: BoxDecoration(color: AppColors.lightBlue, borderRadius: BorderRadius.circular(10)),
              child: Text('$count',
                  style: const TextStyle(color: AppColors.darkBlue, fontWeight: FontWeight.w700, fontSize: 11.5)),
            ),
          ],
        ],
      ),
    );
  }
}

class _EmptyPanel extends StatelessWidget {
  const _EmptyPanel({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return _Panel(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 18),
        child: Row(
          children: [
            Icon(icon, size: 20, color: AppColors.divider),
            const SizedBox(width: 12),
            Expanded(
              child: Text(text, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13, height: 1.35)),
            ),
          ],
        ),
      ),
    );
  }
}

/// One change to the amount, as a small timeline row.
class _ChangeRow extends StatelessWidget {
  const _ChangeRow({required this.entry, required this.last});

  final TopupHistoryEntry entry;
  final bool last;

  @override
  Widget build(BuildContext context) {
    final h = entry;
    final meta = [
      if (h.actorName != null) h.actorName!,
      if (h.at != null) DateFormat('d MMM yyyy, h:mm a').format(h.at!.toLocal()),
    ].join(' · ');
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SizedBox(
            width: 36,
            child: Column(
              children: [
                const SizedBox(height: 14),
                Container(
                  width: 9,
                  height: 9,
                  decoration: const BoxDecoration(color: AppColors.darkBlue, shape: BoxShape.circle),
                ),
                if (!last) Expanded(child: Container(width: 1.5, color: AppColors.divider)),
              ],
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(0, 9, 16, 9),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    (h.comment ?? '').isNotEmpty ? h.comment! : h.action,
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13.5),
                  ),
                  if (meta.isNotEmpty)
                    Text(meta, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _BillRow extends StatelessWidget {
  const _BillRow({required this.bill});

  final ExpenseClaim bill;

  @override
  Widget build(BuildContext context) {
    final b = bill;
    final pettyCash = b.type == 'petty_cash';
    final title = (b.vendorName ?? '').isNotEmpty
        ? b.vendorName!
        : ((b.categoryName ?? '').isNotEmpty ? b.categoryName! : 'Bill #${b.id}');
    final details = [
      if ((b.billDate ?? '').isNotEmpty) b.billDate!,
      if ((b.opNumber ?? '').isNotEmpty) b.opNumber!,
      pettyCash ? 'Petty cash' : 'Reimbursement',
    ].join(' · ');
    return InkWell(
      onTap: () => context.push('/claim/${b.id}'),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: (pettyCash ? AppColors.orange : AppColors.darkBlue).withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                pettyCash ? PhosphorIcons.wallet() : PhosphorIcons.receipt(),
                size: 18,
                color: pettyCash ? AppColors.orange : AppColors.darkBlue,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14), overflow: TextOverflow.ellipsis),
                  const SizedBox(height: 2),
                  Text(details,
                      style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                      overflow: TextOverflow.ellipsis),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(formatMoney(b.currency, b.totalAmount ?? b.amount),
                    style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14)),
                const SizedBox(height: 4),
                StatusChip.forClaim(b),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

Future<void> _openTopupSheet(BuildContext context, WidgetRef ref, RegionConfig region, PettyCashFund pot) async {
  final done = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    builder: (_) => _PrepareTopupSheet(pot: pot),
  );
  if (done == true) {
    _refreshAll(ref, region.id);
    // On the Petty cash screen, show it on Top-ups; an employee's own page lists it already.
    if (context.mounted) DefaultTabController.maybeOf(context)?.animateTo(1);
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
  const _SetPotSheet({required this.region, this.pot, this.employee});

  final RegionConfig region;
  final PettyCashFund? pot;

  /// Opened from this employee's page: no picker.
  final PcaStaff? employee;

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
    _employeeId = widget.pot?.employeeId ?? widget.employee?.id;
    if (!_editing && widget.employee == null) _loadPeople();
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
            if (_editing || widget.employee != null)
              InputDecorator(
                decoration: const InputDecoration(labelText: 'Employee'),
                child: Text(widget.pot?.employeeName ?? widget.employee?.displayName ?? ''),
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

/// A site-model company's petty cash top-ups, with the approve / pay / reject steps for the
/// signed-in role. Also Admin's Company screen tab for that company.
class SiteTopupsView extends ConsumerWidget {
  const SiteTopupsView({super.key, required this.region, required this.role});

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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../api/enums.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/currency.dart';
import '../../widgets/app_nav_drawer.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/pca_fund_figures.dart';
import '../../widgets/region_branding.dart';
import '../pca/accounts_cash_view.dart' show AccountsCashView;
import '../pca/advances_screen.dart' show PcaDepartmentsView, PcaRequestsView;
import '../pca/site_pca_screen.dart' show SitePotsView, SiteTopupsView;
import 'admin_providers.dart';
import 'admin_regions_screen.dart';
import 'limit_amount_sheet.dart';
import 'topups_screen.dart';

class AdminCompanyScreen extends ConsumerWidget {
  const AdminCompanyScreen({super.key, required this.regionId});

  final int regionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(adminRegionsProvider);
    return async.when(
      loading: () => const Scaffold(
        backgroundColor: AppColors.background,
        body: Center(child: CircularProgressIndicator()),
      ),
      error: (e, _) => Scaffold(
        backgroundColor: AppColors.background,
        appBar: const BrandAppBar(title: 'Company', automaticallyImplyLeading: true),
        body: Center(child: Text('$e')),
      ),
      data: (regions) {
        RegionConfig? region;
        for (final r in regions) {
          if (r.id == regionId) region = r;
        }
        if (region == null) {
          return Scaffold(
            backgroundColor: AppColors.background,
            appBar: const BrandAppBar(title: 'Company', automaticallyImplyLeading: true),
            body: const Center(child: Text('Company not found')),
          );
        }
        return _CompanyWorkspace(region: region);
      },
    );
  }
}

class _CompanyWorkspace extends ConsumerStatefulWidget {
  const _CompanyWorkspace({required this.region});
  final RegionConfig region;

  @override
  ConsumerState<_CompanyWorkspace> createState() => _CompanyWorkspaceState();
}

class _CompanyWorkspaceState extends ConsumerState<_CompanyWorkspace> with SingleTickerProviderStateMixin {
  late final TabController _tabs;
  final _search = TextEditingController();

  @override
  void initState() {
    super.initState();
    // Employee-advance company: a 4th tab for the Accounts Department's petty cash.
    _tabs = TabController(length: widget.region.usesEmployeeAdvances ? 4 : 3, vsync: this);
  }

  @override
  void dispose() {
    _tabs.dispose();
    _search.dispose();
    super.dispose();
  }

  Future<void> _refresh() async {
    ref.invalidate(departmentFundsProvider(widget.region.id));
    ref.invalidate(adminFundsProvider);
    ref.invalidate(topupsProvider);
    ref.invalidate(adminRegionsProvider);
  }

  Future<void> _editCompany() async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => EditRegionScreen(region: widget.region)),
    );
    if (!mounted) return;
    ref.invalidate(adminRegionsProvider);
    ref.invalidate(regionBrandingProvider);
  }

  Future<void> _setup(DepartmentFund row) async {
    final amount = await askLimitAmount(
      context: context,
      title: 'Set up ${row.departmentName}',
      confirmLabel: 'Save limit',
      currency: baseCurrencyForRegion(widget.region.regionCode),
    );
    if (amount == null || !mounted) return;
    try {
      await ref.read(apiClientProvider).createFund({
        'region_id': widget.region.id,
        'owner_type': 'department',
        'department_id': row.departmentId,
        'opening_balance': amount,
        'currency': baseCurrencyForRegion(widget.region.regionCode),
      });
      await _refresh();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      }
    }
  }

  Future<void> _change(DepartmentFund row) async {
    final fund = row.fund;
    if (fund == null) return;
    final amount = await askLimitAmount(
      context: context,
      title: 'Change ${row.departmentName} limit',
      confirmLabel: 'Save limit',
      currency: fund.currency,
      initial: fund.approvedLimit,
    );
    if (amount == null || !mounted) return;
    try {
      await ref.read(apiClientProvider).updateFundOpening(fund.id, openingBalance: amount);
      await _refresh();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final region = widget.region;
    final title = companyTitle(region);
    return Scaffold(
      backgroundColor: AppColors.background,
      drawer: const AppNavDrawer(),
      appBar: BrandAppBar(
        title: title,
        automaticallyImplyLeading: true,
        actions: [
          // Admin approves / pays employee advances and top-ups on the Advances screen.
          if (region.usesEmployeeAdvances)
            IconButton(
              tooltip: 'Advance requests',
              onPressed: () => context.push('/advances'),
              icon: Icon(PhosphorIcons.handCoins()),
            ),
          IconButton(
            tooltip: 'Company name and logo',
            onPressed: _editCompany,
            icon: Icon(PhosphorIcons.pencilSimple()),
          ),
        ],
      ),
      body: Column(
        children: [
          _CompanyHeader(region: region, onEdit: _editCompany),
          Material(
            color: AppColors.card,
            child: TabBar(
              controller: _tabs,
              labelColor: AppColors.darkBlue,
              unselectedLabelColor: AppColors.textSecondary,
              indicatorColor: AppColors.orange,
              // Four tabs don't fit a phone's width evenly, so they scroll.
              isScrollable: region.usesEmployeeAdvances,
              tabAlignment: region.usesEmployeeAdvances ? TabAlignment.start : null,
              // Employee-advance company (Professional Signs): no department funding, so the
              // first two tabs are each employee's petty cash and the top-up requests instead,
              // plus the Accounts Department's own petty cash (PDF section 6).
              tabs: region.usesEmployeeAdvances
                  ? const [
                      Tab(text: 'Employees'),
                      Tab(text: 'Requests'),
                      Tab(text: 'Accounts cash'),
                      Tab(text: 'Approvers'),
                    ]
                  // Blue Rhine Contracting: no departments either -- each employee's petty
                  // cash and its top-ups (Accountant -> Head of Accountant -> Finance Manager).
                  : region.usesSitePots
                      ? const [Tab(text: 'Employees'), Tab(text: 'Top-ups'), Tab(text: 'Approvers')]
                      : const [Tab(text: 'Departments'), Tab(text: 'Top-ups'), Tab(text: 'Approvers')],
            ),
          ),
          Expanded(
            child: TabBarView(
              controller: _tabs,
              children: region.usesEmployeeAdvances
                  ? [
                      PcaDepartmentsView(regionId: region.id),
                      const PcaRequestsView(),
                      AccountsCashView(regionId: region.id),
                      _ApproversTab(region: region),
                    ]
                  : region.usesSitePots
                  ? [
                      SitePotsView(region: region, role: UserRole.admin),
                      SiteTopupsView(region: region, role: UserRole.admin),
                      _ApproversTab(region: region),
                    ]
                  : [
                      _DepartmentsTab(
                        region: region,
                        search: _search,
                        onChanged: () => setState(() {}),
                        onSetup: _setup,
                        onChange: _change,
                      ),
                      _CompanyTopupsTab(regionId: region.id),
                      _ApproversTab(region: region),
                    ],
            ),
          ),
        ],
      ),
    );
  }
}

class _CompanyHeader extends StatelessWidget {
  const _CompanyHeader({required this.region, required this.onEdit});

  final RegionConfig region;
  final VoidCallback onEdit;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.card,
      child: InkWell(
        onTap: onEdit,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
          child: Row(
            children: [
              Container(
                width: 72,
                height: 52,
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFFF4F6F8),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: RegionLogo(regionCode: region.regionCode, fit: BoxFit.contain),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      companyTitle(region),
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, height: 1.2),
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        _CodeChip(code: region.regionCode),
                        const SizedBox(width: 8),
                        Text(region.regionName, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                      ],
                    ),
                  ],
                ),
              ),
              Icon(PhosphorIcons.caretRight(), color: AppColors.textSecondary, size: 16),
            ],
          ),
        ),
      ),
    );
  }
}

final _regionApproversProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, int>((ref, regionId) {
  return ref.watch(apiClientProvider).regionApprovers(regionId);
});

class _ApproversTab extends ConsumerWidget {
  const _ApproversTab({required this.region});

  final RegionConfig region;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(_regionApproversProvider(region.id));
    final company = companyTitle(region);
    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('$e')),
      data: (data) {
        final roles = Map<String, dynamic>.from(data['roles'] as Map? ?? const {});
        List<Map<String, dynamic>> people(String role) => [
              for (final p in (roles[role] as List? ?? const [])) Map<String, dynamic>.from(p as Map),
            ];
        // Professional Signs (employee advances) names and describes the steps its own way.
        final ps = region.usesEmployeeAdvances;
        // Blue Rhine Contracting: no HODs -- Accountant -> Head of Accountant -> Finance Manager.
        if (region.usesSitePots) {
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(_regionApproversProvider(region.id)),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
              children: [
                _ApproverSection(
                  title: '1. Accountant',
                  emptyText: 'No Accountant for $company — those bills go to Admin.',
                  people: people('accountant'),
                  company: company,
                  whatTheyApprove: (_) => 'Checks $company bills, sets site petty cash, prepares top-ups',
                ),
                const SizedBox(height: 16),
                _ApproverSection(
                  title: '2. Head of Accountant',
                  emptyText: 'No Head of Accountant for $company — set one in People (App role).',
                  people: people('head_accountant'),
                  company: company,
                  whatTheyApprove: (_) => 'Approves $company bills and top-ups, sets site petty cash',
                ),
                const SizedBox(height: 16),
                _ApproverSection(
                  title: '3. Finance Manager',
                  emptyText: 'No Finance Manager for $company — those bills go to Admin.',
                  people: people('finance_manager'),
                  company: company,
                  whatTheyApprove: (_) => 'Final approval and bank withdrawal for $company',
                ),
              ],
            ),
          );
        }
        return RefreshIndicator(
          onRefresh: () async => ref.invalidate(_regionApproversProvider(region.id)),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
            children: [
              _ApproverSection(
                title: '1. Department HOD',
                emptyText: 'No HOD for $company — those bills go to Admin.',
                people: people('hod'),
                company: company,
                groupByDepartment: true,
                whatTheyApprove: (p) {
                  final dept = (p['department_name'] as String?)?.trim();
                  return dept == null || dept.isEmpty ? 'Approves department bills' : 'Approves $dept bills';
                },
              ),
              // Professional Signs has no Accountant step: Employee -> HOD -> Accounts Manager.
              if (!ps) ...[
                const SizedBox(height: 16),
                _ApproverSection(
                  title: '2. Accountant',
                  emptyText: 'No Accountant for $company — those bills go to Admin.',
                  people: people('accountant'),
                  company: company,
                  whatTheyApprove: (_) => 'Checks all $company bills',
                ),
              ],
              const SizedBox(height: 16),
              _ApproverSection(
                title: ps ? '2. Accounts Manager (Finance Manager role)' : '3. Finance Manager',
                emptyText: ps
                    ? 'No Accounts Manager for $company — those bills go to Admin.'
                    : 'No Finance Manager for $company — those bills go to Admin.',
                people: people('finance_manager'),
                company: company,
                whatTheyApprove: (_) => ps ? 'Accounts Manager for $company' : 'Final approval for $company',
              ),
            ],
          ),
        );
      },
    );
  }
}

class _ApproverSection extends StatelessWidget {
  const _ApproverSection({
    required this.title,
    required this.emptyText,
    required this.people,
    required this.company,
    required this.whatTheyApprove,
    this.groupByDepartment = false,
  });

  final String title;
  final String emptyText;
  final List<Map<String, dynamic>> people;
  final String company;
  final String Function(Map<String, dynamic>) whatTheyApprove;
  final bool groupByDepartment;

  @override
  Widget build(BuildContext context) {
    final groups = <String, List<Map<String, dynamic>>>{};
    if (groupByDepartment) {
      for (final p in people) {
        final dept = ((p['department_name'] as String?) ?? '').trim();
        groups.putIfAbsent(dept.isEmpty ? 'No department' : dept, () => []).add(p);
      }
    } else {
      groups[''] = people;
    }
    final keys = groups.keys.toList()
      ..sort((a, b) {
        if (a == 'No department') return 1;
        if (b == 'No department') return -1;
        return a.toLowerCase().compareTo(b.toLowerCase());
      });

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
        const SizedBox(height: 10),
        if (people.isEmpty)
          Material(
            color: AppColors.warningSoft,
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Text(emptyText),
            ),
          )
        else
          for (final key in keys) ...[
            if (key.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 4, bottom: 6),
                child: Text(
                  key,
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 13,
                    color: AppColors.darkBlue,
                  ),
                ),
              ),
            for (final p in groups[key]!)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: _ApproverCard(person: p, why: whatTheyApprove(p)),
              ),
          ],
      ],
    );
  }
}

class _ApproverCard extends StatelessWidget {
  const _ApproverCard({required this.person, required this.why});

  final Map<String, dynamic> person;
  final String why;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 18,
              backgroundColor: AppColors.lightBlue,
              child: Text(
                _approverInitials(person['display_name'] as String? ?? ''),
                style: const TextStyle(color: AppColors.darkBlue, fontWeight: FontWeight.w800, fontSize: 12),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    person['display_name'] as String? ?? '',
                    style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15),
                  ),
                  const SizedBox(height: 2),
                  Text(why, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12.5)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

String _approverInitials(String name) {
  final parts = name.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
  if (parts.isEmpty) return '?';
  if (parts.length == 1) return parts.first.substring(0, 1).toUpperCase();
  return (parts.first[0] + parts.last[0]).toUpperCase();
}

class _CodeChip extends StatelessWidget {
  const _CodeChip({required this.code});
  final String code;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.lightBlue,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        code.toUpperCase(),
        style: const TextStyle(
          color: AppColors.darkBlue,
          fontWeight: FontWeight.w700,
          fontSize: 11,
          letterSpacing: 0.4,
        ),
      ),
    );
  }
}

class _DepartmentsTab extends ConsumerWidget {
  const _DepartmentsTab({
    required this.region,
    required this.search,
    required this.onChanged,
    required this.onSetup,
    required this.onChange,
  });

  final RegionConfig region;
  final TextEditingController search;
  final VoidCallback onChanged;
  final Future<void> Function(DepartmentFund row) onSetup;
  final Future<void> Function(DepartmentFund row) onChange;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(departmentFundsProvider(region.id));
    final query = search.text.trim().toLowerCase();
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
          child: TextField(
            controller: search,
            onChanged: (_) => onChanged(),
            decoration: InputDecoration(
              hintText: 'Search department',
              prefixIcon: Icon(PhosphorIcons.magnifyingGlass()),
              isDense: true,
            ),
          ),
        ),
        Expanded(
          child: async.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text('$e', textAlign: TextAlign.center),
              ),
            ),
            data: (rows) {
              final visible = [
                for (final row in rows)
                  if (query.isEmpty || row.departmentName.toLowerCase().contains(query)) row,
              ];
              if (visible.isEmpty) {
                return const Center(child: Text('No departments for this company'));
              }
              return ListView.separated(
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 28),
                itemCount: visible.length,
                separatorBuilder: (_, _) => const SizedBox(height: 10),
                itemBuilder: (context, i) {
                  final row = visible[i];
                  return _DepartmentCard(
                    row: row,
                    onSetup: () => onSetup(row),
                    onChange: () => onChange(row),
                  );
                },
              );
            },
          ),
        ),
      ],
    );
  }
}

class _DepartmentCard extends StatelessWidget {
  const _DepartmentCard({
    required this.row,
    required this.onSetup,
    required this.onChange,
  });

  final DepartmentFund row;
  final VoidCallback onSetup;
  final VoidCallback onChange;

  @override
  Widget build(BuildContext context) {
    final fund = row.fund;
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    row.departmentName,
                    style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: fund == null ? AppColors.warningSoft : AppColors.successSoft,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    fund == null ? 'Not set up' : 'Active',
                    style: TextStyle(
                      color: fund == null ? AppColors.orange : AppColors.success,
                      fontWeight: FontWeight.w700,
                      fontSize: 11,
                    ),
                  ),
                ),
              ],
            ),
            if (fund != null) ...[
              const SizedBox(height: 12),
              PcaFundFigures(fund: fund),
            ],
            const SizedBox(height: 12),
            if (fund == null)
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: onSetup,
                  child: const Text('Set up limit'),
                ),
              )
            else
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: onChange,
                  child: const Text('Change limit'),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _CompanyTopupsTab extends ConsumerWidget {
  const _CompanyTopupsTab({required this.regionId});
  final int regionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(topupsProvider);
    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('$e')),
      data: (items) {
        final mine = [
          for (final t in items)
            if (t.fund?.regionId == regionId) t,
        ];
        if (mine.isEmpty) {
          return const Center(child: Text('No top-ups for this company yet'));
        }
        return ListView.separated(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
          itemCount: mine.length,
          separatorBuilder: (_, _) => const SizedBox(height: 10),
          itemBuilder: (context, i) => TopupRequestTile(request: mine[i]),
        );
      },
    );
  }
}

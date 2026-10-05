import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../api/enums.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/money.dart';
import '../../widgets/app_card.dart';
import '../../widgets/brand_app_bar.dart';
import '../authentication/auth_controller.dart';
import '../shared/status_chip.dart';
import 'dashboard_data.dart';

/// Web table of every visible claim (whole company for approvers, own claims for
/// employees) with search, filters, and sortable columns. Rows open the same
/// detail/review screens the mobile app uses.
class AllClaimsScreen extends ConsumerStatefulWidget {
  const AllClaimsScreen({super.key});

  @override
  ConsumerState<AllClaimsScreen> createState() => _AllClaimsScreenState();
}

enum _SortColumn { id, date, employee, vendor, total, status }

class _AllClaimsScreenState extends ConsumerState<AllClaimsScreen> {
  final _search = TextEditingController();
  String? _status;
  String? _region;
  String? _category;
  String? _type;
  bool _flaggedOnly = false;
  _SortColumn _sort = _SortColumn.date;
  bool _ascending = false;

  static const _pageSize = 25;
  int _page = 0;

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  List<ExpenseClaim> _apply(List<ExpenseClaim> claims) {
    final q = _search.text.trim().toLowerCase();
    final filtered = claims.where((c) {
      if (_status != null && c.status != _status) return false;
      if (_region != null && c.regionCode != _region) return false;
      if (_category != null && c.category != _category) return false;
      if (_type != null && c.type != _type) return false;
      if (_flaggedOnly && !(c.duplicateFlag || c.vendorUnmatched)) return false;
      if (q.isEmpty) return true;
      return '${c.id}'.contains(q) ||
          c.vendor.toLowerCase().contains(q) ||
          c.employeeDisplay.toLowerCase().contains(q) ||
          c.category.toLowerCase().contains(q) ||
          (c.opNumber ?? '').toLowerCase().contains(q);
    }).toList();

    int compare(ExpenseClaim a, ExpenseClaim b) => switch (_sort) {
          _SortColumn.id => a.id.compareTo(b.id),
          _SortColumn.date => (claimDate(a) ?? DateTime(0)).compareTo(claimDate(b) ?? DateTime(0)),
          _SortColumn.employee => a.employeeDisplay.toLowerCase().compareTo(b.employeeDisplay.toLowerCase()),
          _SortColumn.vendor => a.vendor.toLowerCase().compareTo(b.vendor.toLowerCase()),
          _SortColumn.total => claimTotal(a).compareTo(claimTotal(b)),
          _SortColumn.status => a.status.compareTo(b.status),
        };
    filtered.sort((a, b) => _ascending ? compare(a, b) : compare(b, a));
    return filtered;
  }

  void _setSort(_SortColumn column, bool ascending) => setState(() {
        _sort = column;
        _ascending = ascending;
      });

  void _resetPage() => _page = 0;

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(visibleClaimsProvider);
    final role = UserRoleX.fromJson(ref.watch(authControllerProvider).user?.role);

    return Scaffold(
      appBar: BrandAppBar(
        title: role.isApprover ? 'All claims' : 'My claims',
        showNotificationAction: false,
        actions: [
          IconButton(
            tooltip: 'Refresh',
            onPressed: () => ref.invalidate(visibleClaimsProvider),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (claims) {
          final rows = _apply(claims);
          final pageCount = (rows.length / _pageSize).ceil().clamp(1, 1 << 30);
          final page = _page.clamp(0, pageCount - 1);
          final pageRows = rows.skip(page * _pageSize).take(_pageSize).toList();
          final regions = claims.map((c) => c.regionCode).whereType<String>().toSet().toList()..sort();
          final categories = claims.map((c) => c.category).where((c) => c.isNotEmpty).toSet().toList()..sort();

          // Per-currency totals for whatever the filters currently match -- never blended.
          final totals = <String, double>{};
          for (final c in rows) {
            totals[c.currency] = (totals[c.currency] ?? 0) + claimTotal(c);
          }

          return ListView(
            padding: const EdgeInsets.fromLTRB(24, 20, 24, 40),
            children: [
              Wrap(
                spacing: 12,
                runSpacing: 10,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  SizedBox(
                    width: 300,
                    child: TextField(
                      controller: _search,
                      onChanged: (_) => setState(_resetPage),
                      decoration: InputDecoration(
                        isDense: true,
                        prefixIcon: const Icon(Icons.search),
                        hintText: role == UserRole.employee ? 'Search vendor, category, #id' : 'Search vendor, employee, #id',
                      ),
                    ),
                  ),
                  _FilterDropdown(
                    hint: 'All statuses',
                    value: _status,
                    items: kStatusLabels,
                    onChanged: (v) => setState(() {
                      _status = v;
                      _resetPage();
                    }),
                  ),
                  if (regions.length > 1)
                    _FilterDropdown(
                      hint: 'All regions',
                      value: _region,
                      items: {for (final r in regions) r: r},
                      onChanged: (v) => setState(() {
                        _region = v;
                        _resetPage();
                      }),
                    ),
                  _FilterDropdown(
                    hint: 'All categories',
                    value: _category,
                    items: {for (final c in categories) c: c},
                    onChanged: (v) => setState(() {
                      _category = v;
                      _resetPage();
                    }),
                  ),
                  _FilterDropdown(
                    hint: 'All types',
                    value: _type,
                    items: const {'reimbursement': 'Reimbursement', 'petty_cash': 'Petty cash'},
                    onChanged: (v) => setState(() {
                      _type = v;
                      _resetPage();
                    }),
                  ),
                  if (role.isApprover)
                    FilterChip(
                      label: const Text('Flagged only'),
                      selected: _flaggedOnly,
                      onSelected: (v) => setState(() {
                        _flaggedOnly = v;
                        _resetPage();
                      }),
                    ),
                ],
              ),
              const SizedBox(height: 14),
              Text(
                [
                  '${rows.length} of ${claims.length} claims',
                  for (final e in totals.entries) formatMoney(e.key, e.value),
                ].join('  ·  '),
                style: const TextStyle(color: AppColors.textSecondary, fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 12),
              AppCard(
                padding: EdgeInsets.zero,
                child: rows.isEmpty
                    ? const Padding(
                        padding: EdgeInsets.all(24),
                        child: Text('No claims match these filters.', style: TextStyle(color: AppColors.textSecondary)),
                      )
                    : LayoutBuilder(builder: (context, constraints) {
                        return SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: ConstrainedBox(
                            constraints: BoxConstraints(minWidth: constraints.maxWidth),
                            child: DataTable(
                              showCheckboxColumn: false,
                              columnSpacing: 22,
                              horizontalMargin: 18,
                              headingRowColor: const WidgetStatePropertyAll(AppColors.background),
                              headingTextStyle: const TextStyle(
                                fontWeight: FontWeight.w700,
                                fontSize: 12,
                                color: AppColors.textSecondary,
                              ),
                              dataTextStyle: const TextStyle(fontSize: 13, color: AppColors.textPrimary),
                              sortColumnIndex: _sortIndex(role),
                              sortAscending: _ascending,
                              columns: _columns(role),
                              rows: [for (final c in pageRows) _row(context, c, role)],
                            ),
                          ),
                        );
                      }),
              ),
              if (pageCount > 1) ...[
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    Text('Page ${page + 1} of $pageCount', style: const TextStyle(color: AppColors.textSecondary)),
                    const SizedBox(width: 8),
                    IconButton(
                      onPressed: page == 0 ? null : () => setState(() => _page = page - 1),
                      icon: const Icon(Icons.chevron_left),
                    ),
                    IconButton(
                      onPressed: page >= pageCount - 1 ? null : () => setState(() => _page = page + 1),
                      icon: const Icon(Icons.chevron_right),
                    ),
                  ],
                ),
              ],
            ],
          );
        },
      ),
    );
  }

  // Column order must match _row(); the employee column only exists for approvers.
  List<_SortColumn?> _columnKeys(UserRole role) => [
        _SortColumn.id,
        _SortColumn.date,
        if (role.isApprover) _SortColumn.employee,
        _SortColumn.vendor,
        null, // category
        null, // region
        _SortColumn.total,
        _SortColumn.status,
        null, // stage
        null, // flags
      ];

  int? _sortIndex(UserRole role) {
    final i = _columnKeys(role).indexOf(_sort);
    return i < 0 ? null : i;
  }

  List<DataColumn> _columns(UserRole role) {
    const labels = {
      _SortColumn.id: '#',
      _SortColumn.date: 'Submitted',
      _SortColumn.employee: 'Employee',
      _SortColumn.vendor: 'Vendor',
      _SortColumn.total: 'Total',
      _SortColumn.status: 'Status',
    };
    final unsortable = ['Category', 'Region', 'Stage', 'Flags'];
    var u = 0;
    return [
      for (final key in _columnKeys(role))
        if (key == null)
          DataColumn(label: Text(unsortable[u++]))
        else
          DataColumn(
            label: Text(labels[key]!),
            numeric: key == _SortColumn.total,
            onSort: (_, asc) => _setSort(key, asc),
          ),
    ];
  }

  DataRow _row(BuildContext context, ExpenseClaim c, UserRole role) {
    final date = claimDate(c);
    final stage = kPendingStatuses.contains(c.status) ? (kStageLabels[c.currentStage] ?? '-') : '-';
    return DataRow(
      onSelectChanged: (_) => openClaim(context, c, role),
      cells: [
        DataCell(Text('${c.id}')),
        DataCell(Text(date == null ? '-' : DateFormat('d MMM yyyy').format(date.toLocal()))),
        if (role.isApprover) DataCell(Text(c.employeeDisplay)),
        DataCell(ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 220),
          child: Text(c.vendor.isEmpty ? '-' : c.vendor, overflow: TextOverflow.ellipsis),
        )),
        DataCell(Text(c.category.isEmpty ? '-' : c.category)),
        DataCell(Text(c.regionCode ?? '-')),
        DataCell(Text(formatMoney(c.currency, claimTotal(c)), style: const TextStyle(fontWeight: FontWeight.w600))),
        DataCell(StatusChip(status: c.status)),
        DataCell(Text(stage)),
        DataCell(Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (c.duplicateFlag)
              const Tooltip(
                message: 'Possible duplicate (same employee, vendor, amount and date)',
                child: Icon(Icons.content_copy, size: 16, color: AppColors.orange),
              ),
            if (c.duplicateFlag && c.vendorUnmatched) const SizedBox(width: 6),
            if (c.vendorUnmatched)
              const Tooltip(
                message: 'Vendor not matched yet (Accountant resolves)',
                child: Icon(Icons.storefront_outlined, size: 16, color: AppColors.orange),
              ),
            if (c.type == 'petty_cash') ...[
              const SizedBox(width: 6),
              const Tooltip(message: 'Petty cash', child: Icon(Icons.account_balance_wallet_outlined, size: 16, color: AppColors.darkBlue)),
            ],
          ],
        )),
      ],
    );
  }
}

class _FilterDropdown extends StatelessWidget {
  const _FilterDropdown({required this.hint, required this.value, required this.items, required this.onChanged});

  final String hint;
  final String? value;
  final Map<String, String> items;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: value == null ? AppColors.divider : AppColors.darkBlue),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String?>(
          value: value,
          hint: Text(hint),
          borderRadius: BorderRadius.circular(12),
          items: [
            DropdownMenuItem<String?>(value: null, child: Text(hint)),
            for (final e in items.entries) DropdownMenuItem<String?>(value: e.key, child: Text(e.value)),
          ],
          onChanged: onChanged,
        ),
      ),
    );
  }
}

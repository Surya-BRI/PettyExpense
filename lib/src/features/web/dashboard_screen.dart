import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../api/enums.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/dubai_time.dart';
import '../../utils/money.dart';
import '../../widgets/app_card.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/shimmer_box.dart';
import '../authentication/auth_controller.dart';
import '../shared/status_chip.dart';
import 'dashboard_data.dart';

/// Web overview: totals and breakdowns of everything moving through the app.
/// Money is never summed across currencies -- one currency is shown at a time.
class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  DashboardPeriod _period = DashboardPeriod.all;
  String? _region; // null = all regions
  String? _currency; // null = most common currency in the data

  void _refresh() {
    ref.invalidate(visibleClaimsProvider);
    ref.invalidate(activityFeedProvider);
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(visibleClaimsProvider);
    final user = ref.watch(authControllerProvider).user;
    final role = UserRoleX.fromJson(user?.role);

    return Scaffold(
      appBar: BrandAppBar(
        title: 'Dashboard',
        showNotificationAction: false,
        actions: [
          IconButton(tooltip: 'Refresh', onPressed: _refresh, icon: const Icon(Icons.refresh)),
        ],
      ),
      body: async.when(
        loading: () => const _DashboardSkeleton(),
        error: (e, _) => Center(child: Text('$e')),
        data: (claims) => _buildBody(context, claims, role, user),
      ),
    );
  }

  Widget _buildBody(BuildContext context, List<ExpenseClaim> claims, UserRole role, AuthUser? user) {
    final now = DateTime.now();
    final currencyCounts = <String, int>{};
    for (final c in claims) {
      currencyCounts[c.currency] = (currencyCounts[c.currency] ?? 0) + 1;
    }
    final currencies = currencyCounts.keys.toList()..sort();
    final mostCommon = currencyCounts.entries.isEmpty
        ? 'AED'
        : currencyCounts.entries.reduce((a, b) => a.value >= b.value ? a : b).key;
    final currency = (_currency != null && currencies.contains(_currency)) ? _currency! : mostCommon;
    final regions = claims.map((c) => c.regionCode).whereType<String>().toSet().toList()..sort();

    final scoped = claims
        .where((c) => c.currency == currency && (_region == null || c.regionCode == _region))
        .toList();
    final inPeriod = scoped.where((c) => _period.includes(claimDate(c), now)).toList();

    final approver = role.isApprover;
    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 40),
      children: [
        Text(
          approver ? 'Overview' : 'My overview',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 4),
        Text(
          approver
              ? 'Every claim across the company, ${_period.label.toLowerCase()}.'
              : 'Your claims, ${_period.label.toLowerCase()}.',
          style: const TextStyle(color: AppColors.textSecondary),
        ),
        const SizedBox(height: 16),
        _FilterBar(
          period: _period,
          onPeriod: (p) => setState(() => _period = p),
          regions: regions,
          region: _region,
          onRegion: (r) => setState(() => _region = r),
          currencies: currencies.isEmpty ? [currency] : currencies,
          currency: currency,
          onCurrency: (c) => setState(() => _currency = c),
        ),
        const SizedBox(height: 16),
        _KpiRow(claims: inPeriod, currency: currency),
        const SizedBox(height: 16),
        _TwoColumn(
          left: _StatusCard(claims: inPeriod, currency: currency),
          right: _StageCard(claims: inPeriod, currency: currency),
        ),
        const SizedBox(height: 16),
        _TwoColumn(
          left: _CategoryCard(claims: inPeriod, currency: currency),
          right: _MonthlyCard(claims: scoped, currency: currency, now: now),
        ),
        const SizedBox(height: 16),
        if (approver) ...[
          _TwoColumn(
            left: _TopEmployeesCard(claims: inPeriod, currency: currency),
            right: _AttentionCard(claims: inPeriod, role: role),
          ),
          const SizedBox(height: 16),
          _TwoColumn(
            left: _ActivityCard(claims: claims, role: role),
            right: _LatestClaimsCard(claims: inPeriod, role: role),
          ),
        ] else
          _TwoColumn(
            left: _AttentionCard(claims: inPeriod, role: role),
            right: _LatestClaimsCard(claims: inPeriod, role: role),
          ),
      ],
    );
  }
}

// ---------------------------------------------------------------------------
// Layout helpers
// ---------------------------------------------------------------------------

class _TwoColumn extends StatelessWidget {
  const _TwoColumn({required this.left, required this.right});

  final Widget left;
  final Widget right;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      if (constraints.maxWidth < 900) {
        return Column(children: [left, const SizedBox(height: 16), right]);
      }
      return Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(child: left),
          const SizedBox(width: 16),
          Expanded(child: right),
        ],
      );
    });
  }
}

class _Panel extends StatelessWidget {
  const _Panel({required this.title, this.subtitle, required this.child, this.trailing});

  final String title;
  final String? subtitle;
  final Widget child;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      padding: const EdgeInsets.fromLTRB(18, 16, 18, 18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
                    if (subtitle != null) ...[
                      const SizedBox(height: 2),
                      Text(subtitle!, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                    ],
                  ],
                ),
              ),
              ?trailing,
            ],
          ),
          const SizedBox(height: 14),
          child,
        ],
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: Text(text, style: const TextStyle(color: AppColors.textSecondary)),
    );
  }
}

// ---------------------------------------------------------------------------
// Filters
// ---------------------------------------------------------------------------

class _FilterBar extends StatelessWidget {
  const _FilterBar({
    required this.period,
    required this.onPeriod,
    required this.regions,
    required this.region,
    required this.onRegion,
    required this.currencies,
    required this.currency,
    required this.onCurrency,
  });

  final DashboardPeriod period;
  final ValueChanged<DashboardPeriod> onPeriod;
  final List<String> regions;
  final String? region;
  final ValueChanged<String?> onRegion;
  final List<String> currencies;
  final String currency;
  final ValueChanged<String> onCurrency;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 12,
      runSpacing: 10,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        _DropdownPill<DashboardPeriod>(
          icon: Icons.calendar_today_outlined,
          value: period,
          items: {for (final p in DashboardPeriod.values) p: p.label},
          onChanged: (v) => onPeriod(v ?? DashboardPeriod.all),
        ),
        _DropdownPill<String?>(
          icon: Icons.public,
          value: region,
          items: {null: 'All regions', for (final r in regions) r: r},
          onChanged: onRegion,
        ),
        SegmentedButton<String>(
          showSelectedIcon: false,
          segments: [for (final c in currencies) ButtonSegment(value: c, label: Text(c))],
          selected: {currency},
          onSelectionChanged: (s) => onCurrency(s.first),
        ),
      ],
    );
  }
}

class _DropdownPill<T> extends StatelessWidget {
  const _DropdownPill({required this.icon, required this.value, required this.items, required this.onChanged});

  final IconData icon;
  final T value;
  final Map<T, String> items;
  final ValueChanged<T?> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.only(left: 12, right: 6),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.divider),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: AppColors.darkBlue),
          const SizedBox(width: 8),
          DropdownButtonHideUnderline(
            child: DropdownButton<T>(
              value: value,
              borderRadius: BorderRadius.circular(12),
              items: [
                for (final e in items.entries) DropdownMenuItem<T>(value: e.key, child: Text(e.value)),
              ],
              onChanged: onChanged,
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// KPI tiles
// ---------------------------------------------------------------------------

class _KpiRow extends StatelessWidget {
  const _KpiRow({required this.claims, required this.currency});

  final List<ExpenseClaim> claims;
  final String currency;

  @override
  Widget build(BuildContext context) {
    double sum(Iterable<ExpenseClaim> xs) => xs.fold(0.0, (a, c) => a + claimTotal(c));
    final claimed = claims.where((c) => c.status != 'draft' && c.status != 'rejected').toList();
    final pending = claims.where((c) => kPendingStatuses.contains(c.status)).toList();
    final disputed = pending.where((c) => c.status == 'disputed').length;
    final approved = claims.where((c) => c.status == 'approved').toList();
    final paid = claims.where((c) => c.status == 'paid').toList();
    final rejected = claims.where((c) => c.status == 'rejected').toList();
    final drafts = claims.where((c) => c.status == 'draft').length;

    final tiles = [
      _KpiTile(
        label: 'Total claimed',
        value: formatMoney(currency, sum(claimed)),
        detail: '${claimed.length} claims${drafts > 0 ? ' · $drafts drafts' : ''}',
        icon: Icons.receipt_long,
        accent: AppColors.brightBlue,
      ),
      _KpiTile(
        label: 'Pending approval',
        value: formatMoney(currency, sum(pending)),
        detail: '${pending.length} claims${disputed > 0 ? ' · $disputed disputed' : ''}',
        icon: Icons.hourglass_top,
        accent: AppColors.orange,
      ),
      _KpiTile(
        label: 'Approved, unpaid',
        value: formatMoney(currency, sum(approved)),
        detail: '${approved.length} claims awaiting payment',
        icon: Icons.check_circle_outline,
        accent: AppColors.success,
      ),
      _KpiTile(
        label: 'Paid out',
        value: formatMoney(currency, sum(paid)),
        detail: '${paid.length} claims',
        icon: Icons.payments_outlined,
        accent: AppColors.darkBlue,
      ),
      _KpiTile(
        label: 'Rejected',
        value: formatMoney(currency, sum(rejected)),
        detail: '${rejected.length} claims',
        icon: Icons.block,
        accent: AppColors.danger,
      ),
    ];

    return LayoutBuilder(builder: (context, constraints) {
      final w = constraints.maxWidth;
      final cols = w >= 1100 ? 5 : w >= 820 ? 3 : w >= 520 ? 2 : 1;
      const gap = 16.0;
      final tileWidth = (w - gap * (cols - 1)) / cols;
      return Wrap(
        spacing: gap,
        runSpacing: gap,
        children: [for (final t in tiles) SizedBox(width: tileWidth, child: t)],
      );
    });
  }
}

class _KpiTile extends StatelessWidget {
  const _KpiTile({
    required this.label,
    required this.value,
    required this.detail,
    required this.icon,
    required this.accent,
  });

  final String label;
  final String value;
  final String detail;
  final IconData icon;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(color: accent.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(12)),
            child: Icon(icon, color: accent, size: 22),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                const SizedBox(height: 4),
                FittedBox(
                  fit: BoxFit.scaleDown,
                  alignment: Alignment.centerLeft,
                  child: Text(
                    value,
                    style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                  ),
                ),
                const SizedBox(height: 2),
                Text(detail, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Horizontal bar list (single hue -- magnitude only, no legend needed)
// ---------------------------------------------------------------------------

class _BarItem {
  const _BarItem(this.label, this.value, this.valueLabel, this.tooltip);

  final String label;
  final double value;
  final String valueLabel;
  final String tooltip;
}

class _BarList extends StatelessWidget {
  const _BarList({required this.items, this.emptyText = 'No claims for this filter.'});

  final List<_BarItem> items;
  final String emptyText;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return _Empty(emptyText);
    final maxValue = items.map((i) => i.value).fold<double>(0, math.max);
    return Column(
      children: [
        for (final item in items)
          Tooltip(
            message: item.tooltip,
            waitDuration: const Duration(milliseconds: 150),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 7),
              child: Row(
                children: [
                  SizedBox(
                    width: 130,
                    child: Text(item.label, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 13)),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: LayoutBuilder(builder: (context, constraints) {
                      final frac = maxValue <= 0 ? 0.0 : item.value / maxValue;
                      return Align(
                        alignment: Alignment.centerLeft,
                        child: Container(
                          width: math.max(frac * constraints.maxWidth, item.value > 0 ? 3 : 0),
                          height: 10,
                          decoration: const BoxDecoration(
                            color: AppColors.darkBlue,
                            borderRadius: BorderRadius.horizontal(right: Radius.circular(4)),
                          ),
                        ),
                      );
                    }),
                  ),
                  const SizedBox(width: 10),
                  SizedBox(
                    width: 120,
                    child: Text(
                      item.valueLabel,
                      textAlign: TextAlign.right,
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
                    ),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

class _StatusCard extends StatelessWidget {
  const _StatusCard({required this.claims, required this.currency});

  final List<ExpenseClaim> claims;
  final String currency;

  @override
  Widget build(BuildContext context) {
    final items = <_BarItem>[];
    for (final status in kStatusLabels.keys) {
      final group = claims.where((c) => c.status == status).toList();
      if (group.isEmpty) continue;
      final total = group.fold(0.0, (a, c) => a + claimTotal(c));
      items.add(_BarItem(
        kStatusLabels[status]!,
        group.length.toDouble(),
        '${group.length}',
        '${kStatusLabels[status]}: ${group.length} claims · ${formatMoney(currency, total)}',
      ));
    }
    return _Panel(title: 'Claims by status', subtitle: 'Number of claims', child: _BarList(items: items));
  }
}

class _StageCard extends StatelessWidget {
  const _StageCard({required this.claims, required this.currency});

  final List<ExpenseClaim> claims;
  final String currency;

  @override
  Widget build(BuildContext context) {
    final pending = claims.where((c) => kPendingStatuses.contains(c.status)).toList();
    final items = <_BarItem>[];
    for (final stage in const ['hod', 'department_hod', 'accountant', 'finance_manager']) {
      final group = pending.where((c) => c.currentStage == stage).toList();
      if (group.isEmpty) continue;
      final total = group.fold(0.0, (a, c) => a + claimTotal(c));
      final disputed = group.where((c) => c.status == 'disputed').length;
      items.add(_BarItem(
        kStageLabels[stage]!,
        group.length.toDouble(),
        '${group.length}',
        '${group.length} claims · ${formatMoney(currency, total)}'
            '${disputed > 0 ? ' · $disputed disputed (with employee)' : ''}',
      ));
    }
    // Submitted claims the approval engine hasn't assigned a stage to yet.
    final unassigned = pending.where((c) => c.currentStage == null).length;
    if (unassigned > 0) {
      items.add(_BarItem('Not yet routed', unassigned.toDouble(), '$unassigned', '$unassigned claims awaiting first routing'));
    }
    return _Panel(
      title: 'Where claims are waiting',
      subtitle: 'Pending claims per approval stage',
      child: _BarList(items: items, emptyText: 'Nothing is waiting for approval.'),
    );
  }
}

class _CategoryCard extends StatelessWidget {
  const _CategoryCard({required this.claims, required this.currency});

  final List<ExpenseClaim> claims;
  final String currency;

  @override
  Widget build(BuildContext context) {
    final spend = claims.where((c) => c.status != 'draft' && c.status != 'rejected');
    final totals = <String, double>{};
    final counts = <String, int>{};
    for (final c in spend) {
      final key = c.category.isEmpty ? 'Other' : c.category;
      totals[key] = (totals[key] ?? 0) + claimTotal(c);
      counts[key] = (counts[key] ?? 0) + 1;
    }
    final sorted = totals.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
    // Top 6 shown individually; the tail folds into "Other" rather than growing the list.
    final top = sorted.take(6).toList();
    final rest = sorted.skip(6);
    final items = [
      for (final e in top)
        _BarItem(e.key, e.value, formatMoney(currency, e.value), '${e.key}: ${counts[e.key]} claims · ${formatMoney(currency, e.value)}'),
      if (rest.isNotEmpty)
        () {
          final v = rest.fold(0.0, (a, e) => a + e.value);
          return _BarItem('Other', v, formatMoney(currency, v), '${rest.length} more categories · ${formatMoney(currency, v)}');
        }(),
    ];
    return _Panel(
      title: 'Spend by category',
      subtitle: 'Claimed total, excluding drafts and rejected',
      child: _BarList(items: items),
    );
  }
}

// ---------------------------------------------------------------------------
// Monthly spend (change over time -- last 6 months, single hue)
// ---------------------------------------------------------------------------

class _MonthlyCard extends StatelessWidget {
  const _MonthlyCard({required this.claims, required this.currency, required this.now});

  final List<ExpenseClaim> claims;
  final String currency;
  final DateTime now;

  @override
  Widget build(BuildContext context) {
    final months = [for (var i = 5; i >= 0; i--) DateTime(now.year, now.month - i)];
    final totals = <DateTime, double>{for (final m in months) m: 0};
    final counts = <DateTime, int>{for (final m in months) m: 0};
    for (final c in claims) {
      if (c.status == 'draft' || c.status == 'rejected') continue;
      final d = claimDate(c);
      if (d == null) continue;
      final key = DateTime(d.year, d.month);
      if (!totals.containsKey(key)) continue;
      totals[key] = totals[key]! + claimTotal(c);
      counts[key] = counts[key]! + 1;
    }
    final maxValue = totals.values.fold<double>(0, math.max);
    final monthFmt = DateFormat('MMM');
    const chartHeight = 150.0;

    return _Panel(
      title: 'Monthly spend',
      subtitle: 'Last 6 months, by submission date (ignores the period filter)',
      child: maxValue <= 0
          ? const _Empty('No claims submitted in the last 6 months.')
          : SizedBox(
              height: chartHeight + 44,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  for (final m in months)
                    Expanded(
                      child: Tooltip(
                        message: '${DateFormat('MMMM yyyy').format(m)}: ${counts[m]} claims · ${formatMoney(currency, totals[m]!)}',
                        waitDuration: const Duration(milliseconds: 150),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            // Direct label only on the current month -- not on every bar.
                            if (m == months.last)
                              Padding(
                                padding: const EdgeInsets.only(bottom: 4),
                                child: Text(
                                  NumberFormat.compact().format(totals[m]),
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                                ),
                              ),
                            Container(
                              width: 28,
                              height: math.max(chartHeight * (totals[m]! / maxValue), totals[m]! > 0 ? 3 : 0),
                              decoration: const BoxDecoration(
                                color: AppColors.darkBlue,
                                borderRadius: BorderRadius.vertical(top: Radius.circular(4)),
                              ),
                            ),
                            Container(height: 1, color: AppColors.divider),
                            const SizedBox(height: 6),
                            Text(monthFmt.format(m), style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
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

// ---------------------------------------------------------------------------
// Top employees (approvers only)
// ---------------------------------------------------------------------------

class _TopEmployeesCard extends StatelessWidget {
  const _TopEmployeesCard({required this.claims, required this.currency});

  final List<ExpenseClaim> claims;
  final String currency;

  @override
  Widget build(BuildContext context) {
    final byEmployee = <String, List<ExpenseClaim>>{};
    for (final c in claims.where((c) => c.status != 'draft')) {
      byEmployee.putIfAbsent(c.employeeDisplay, () => []).add(c);
    }
    final rows = byEmployee.entries.map((e) {
      final active = e.value.where((c) => c.status != 'rejected');
      return (
        name: e.key,
        count: e.value.length,
        total: active.fold(0.0, (a, c) => a + claimTotal(c)),
        pending: e.value.where((c) => kPendingStatuses.contains(c.status)).fold(0.0, (a, c) => a + claimTotal(c)),
      );
    }).toList()
      ..sort((a, b) => b.total.compareTo(a.total));

    const header = TextStyle(fontSize: 12, color: AppColors.textSecondary, fontWeight: FontWeight.w600);
    return _Panel(
      title: 'Top employees',
      subtitle: 'By claimed total, excluding rejected',
      child: rows.isEmpty
          ? const _Empty('No submitted claims for this filter.')
          : Column(
              children: [
                const Row(
                  children: [
                    Expanded(flex: 3, child: Text('Employee', style: header)),
                    Expanded(child: Text('Claims', style: header, textAlign: TextAlign.right)),
                    Expanded(flex: 2, child: Text('Claimed', style: header, textAlign: TextAlign.right)),
                    Expanded(flex: 2, child: Text('Pending', style: header, textAlign: TextAlign.right)),
                  ],
                ),
                const Divider(height: 18),
                for (final r in rows.take(8))
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    child: Row(
                      children: [
                        Expanded(flex: 3, child: Text(r.name, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w600))),
                        Expanded(child: Text('${r.count}', textAlign: TextAlign.right)),
                        Expanded(flex: 2, child: Text(formatMoney(currency, r.total), textAlign: TextAlign.right)),
                        Expanded(
                          flex: 2,
                          child: Text(
                            r.pending > 0 ? formatMoney(currency, r.pending) : '-',
                            textAlign: TextAlign.right,
                            style: const TextStyle(color: AppColors.textSecondary),
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
    );
  }
}

// ---------------------------------------------------------------------------
// Needs attention
// ---------------------------------------------------------------------------

class _AttentionCard extends StatelessWidget {
  const _AttentionCard({required this.claims, required this.role});

  final List<ExpenseClaim> claims;
  final UserRole role;

  @override
  Widget build(BuildContext context) {
    final open = claims.where((c) => kPendingStatuses.contains(c.status)).toList();
    final duplicates = open.where((c) => c.duplicateFlag).toList();
    final unmatched = open.where((c) => c.vendorUnmatched).toList();
    final disputed = open.where((c) => c.status == 'disputed').toList();
    final drafts = claims.where((c) => c.status == 'draft').toList();

    final groups = role.isApprover
        ? [
            (Icons.content_copy, 'Possible duplicates', duplicates),
            (Icons.storefront_outlined, 'Unmatched vendors', unmatched),
            (Icons.undo, 'Disputed, with the employee', disputed),
          ]
        : [
            (Icons.undo, 'Sent back to you for correction', disputed),
            (Icons.edit_note, 'Drafts not yet submitted', drafts),
          ];

    final flagged = <ExpenseClaim>{for (final g in groups) ...g.$3}.toList();
    return _Panel(
      title: 'Needs attention',
      subtitle: role.isApprover ? 'Open claims carrying a flag' : 'Your claims that need an action',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              for (final g in groups)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    color: g.$3.isEmpty ? AppColors.background : AppColors.warningSoft,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.divider),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(g.$1, size: 18, color: g.$3.isEmpty ? AppColors.textSecondary : AppColors.orange),
                      const SizedBox(width: 8),
                      Text('${g.$3.length}', style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                      const SizedBox(width: 6),
                      Text(g.$2, style: const TextStyle(fontSize: 13)),
                    ],
                  ),
                ),
            ],
          ),
          const SizedBox(height: 10),
          if (flagged.isEmpty)
            const _Empty('All clear.')
          else
            for (final c in flagged.take(6)) _ClaimRow(claim: c, role: role),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Activity + latest claims
// ---------------------------------------------------------------------------

class _ActivityCard extends ConsumerWidget {
  const _ActivityCard({required this.claims, required this.role});

  final List<ExpenseClaim> claims;
  final UserRole role;

  static const _verbs = {
    'approve': 'approved',
    'dispute': 'disputed',
    'reject': 'rejected',
    'submitted': 'submitted',
    'created': 'saved a draft of',
    'edited': 'edited',
    'paid': 'marked paid',
    'vendor_resolved': 'resolved the vendor on',
  };

  (IconData, Color) _iconFor(String action) => switch (action) {
        'approve' => (Icons.check_circle, AppColors.success),
        'dispute' => (Icons.undo, AppColors.orange),
        'reject' => (Icons.cancel, AppColors.danger),
        'submitted' => (Icons.send, AppColors.brightBlue),
        'paid' => (Icons.payments, AppColors.darkBlue),
        'vendor_resolved' => (Icons.storefront, AppColors.darkBlue),
        _ => (Icons.edit, AppColors.textSecondary),
      };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(activityFeedProvider);
    final byId = {for (final c in claims) c.id: c};
    return _Panel(
      title: 'Recent activity',
      subtitle: 'Every approval-workflow event, newest first',
      child: async.when(
        loading: () => const Padding(
          padding: EdgeInsets.symmetric(vertical: 16),
          child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
        ),
        error: (e, _) => _Empty('$e'),
        data: (items) {
          if (items == null) {
            return const _Empty('Activity feed is not available on this server yet.');
          }
          if (items.isEmpty) return const _Empty('No activity yet.');
          return Column(
            children: [
              for (final a in items.take(12))
                InkWell(
                  borderRadius: BorderRadius.circular(10),
                  onTap: byId[a.transactionId] == null ? null : () => openClaim(context, byId[a.transactionId]!, role),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(_iconFor(a.action).$1, color: _iconFor(a.action).$2, size: 20),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text.rich(
                                TextSpan(children: [
                                  TextSpan(text: a.actorName ?? 'Someone', style: const TextStyle(fontWeight: FontWeight.w700)),
                                  TextSpan(text: ' ${_verbs[a.action] ?? a.action} claim #${a.transactionId}'),
                                  if (a.vendorName != null) TextSpan(text: ' · ${a.vendorName}'),
                                ]),
                                style: const TextStyle(fontSize: 13),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                [
                                  if (a.stage != null && a.stage != 'employee') kStageLabels[a.stage] ?? a.stage!,
                                  if (a.totalAmount != null && a.currency != null) formatMoney(a.currency!, a.totalAmount!),
                                  formatDubaiTime(a.createdAt),
                                ].join(' · '),
                                style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                              ),
                              if (a.comment != null && a.comment!.trim().isNotEmpty)
                                Padding(
                                  padding: const EdgeInsets.only(top: 2),
                                  child: Text(
                                    '"${a.comment!.trim()}"',
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(fontSize: 12, fontStyle: FontStyle.italic),
                                  ),
                                ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _LatestClaimsCard extends StatelessWidget {
  const _LatestClaimsCard({required this.claims, required this.role});

  final List<ExpenseClaim> claims;
  final UserRole role;

  @override
  Widget build(BuildContext context) {
    final sorted = List<ExpenseClaim>.from(claims)
      ..sort((a, b) => (claimDate(b) ?? DateTime(0)).compareTo(claimDate(a) ?? DateTime(0)));
    return _Panel(
      title: 'Latest claims',
      trailing: TextButton(onPressed: () => context.go('/all-claims'), child: const Text('View all')),
      child: sorted.isEmpty
          ? const _Empty('No claims for this filter.')
          : Column(children: [for (final c in sorted.take(8)) _ClaimRow(claim: c, role: role)]),
    );
  }
}

class _ClaimRow extends StatelessWidget {
  const _ClaimRow({required this.claim, required this.role});

  final ExpenseClaim claim;
  final UserRole role;

  @override
  Widget build(BuildContext context) {
    final date = claimDate(claim);
    return InkWell(
      borderRadius: BorderRadius.circular(10),
      onTap: () => openClaim(context, claim, role),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    claim.vendor.isEmpty ? 'Claim #${claim.id}' : claim.vendor,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    [
                      '#${claim.id}',
                      if (role.isApprover) claim.employeeDisplay,
                      if (claim.category.isNotEmpty) claim.category,
                      if (date != null) DateFormat('d MMM yyyy').format(date.toLocal()),
                    ].join(' · '),
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 10),
            Text(formatMoney(claim.currency, claimTotal(claim)), style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
            const SizedBox(width: 10),
            StatusChip(status: claim.status),
          ],
        ),
      ),
    );
  }
}

class _DashboardSkeleton extends StatelessWidget {
  const _DashboardSkeleton();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(24),
      physics: const NeverScrollableScrollPhysics(),
      children: const [
        ShimmerBox(height: 26, widthFraction: 0.25),
        SizedBox(height: 20),
        ShimmerBox(height: 96),
        SizedBox(height: 16),
        ShimmerBox(height: 220),
        SizedBox(height: 16),
        ShimmerBox(height: 220),
      ],
    );
  }
}

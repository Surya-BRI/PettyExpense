import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../api/enums.dart';
import '../api/models.dart';
import '../features/admin/my_funds_screen.dart' show myFundsProvider;
import '../features/authentication/auth_controller.dart';
import '../features/claims/confirm_claim_screen.dart' show navigateGuarded;
import '../features/notifications/notifications_screen.dart';
import '../features/pca/advances_screen.dart' show myPcaAdvancesProvider;
import '../routing/role_routes.dart';
import '../theme/app_theme.dart';
import '../utils/money.dart';
import 'region_branding.dart';

/// Left-hand drawer mirroring the bottom nav bar (see MainShell) -- same destinations,
/// role-aware, for screens that want a menu entry point instead of (or alongside) the
/// bottom bar.
class AppNavDrawer extends ConsumerWidget {
  const AppNavDrawer({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    final role = UserRoleX.fromJson(user?.role);
    final isApprover = role.isApprover;
    final isFinanceManager = role == UserRole.financeManager;
    final isAdmin = role == UserRole.admin;
    final isHod = role == UserRole.hod;
    final isAccountant = role == UserRole.accountant;
    // Professional Signs: petty cash is one advance per employee, not per department.
    final employeeAdvances = user?.usesEmployeeAdvances ?? false;
    // An employee who also belongs to KSA sees "My advances" while signed in under Dubai too.
    final hasOwnAdvance = role == UserRole.employee &&
        (ref.watch(myPcaAdvancesProvider).valueOrNull ?? const <PettyCashFund>[]).isNotEmpty;
    final location = GoRouterState.of(context).uri.path;
    final unreadCount = ref.watch(unreadNotificationCountProvider).maybeWhen(data: (n) => n, orElse: () => 0);

    void go(String path) {
      navigateGuarded(ref, () {
        Navigator.of(context).pop();
        context.go(path);
      });
    }

    // For an employee, Home and Claims are the same screen (homeRouteFor == '/claims'),
    // so only approvers (whose Home is the approvals queue, distinct from Claims) need
    // both entries.
    final items = <_DrawerItem>[
      if (isApprover && !isAdmin)
        _DrawerItem(
          icon: PhosphorIcons.wallet(),
          selectedIcon: PhosphorIcons.wallet(PhosphorIconsStyle.fill),
          accent: AppColors.darkBlue,
          label: 'Claims',
          selected: location.startsWith('/approvals'),
          onTap: () => go('/approvals/${defaultStageFor(role)}'),
        )
      else if (!isAdmin)
        _DrawerItem(
          icon: PhosphorIcons.receipt(),
          selectedIcon: PhosphorIcons.receipt(PhosphorIconsStyle.fill),
          accent: AppColors.darkBlue,
          label: 'Claims',
          selected: location == '/claims' || location.startsWith('/claim/'),
          onTap: () => go('/claims'),
        ),
      if (isFinanceManager || isAdmin)
        _DrawerItem(
          icon: PhosphorIcons.money(),
          selectedIcon: PhosphorIcons.money(PhosphorIconsStyle.fill),
          accent: AppColors.success,
          label: 'Payments',
          selected: location == '/payments',
          onTap: () => go('/payments'),
        ),
      if (employeeAdvances || isAdmin || hasOwnAdvance)
        _DrawerItem(
          icon: PhosphorIcons.handCoins(),
          selectedIcon: PhosphorIcons.handCoins(PhosphorIconsStyle.fill),
          accent: AppColors.orange,
          label: role == UserRole.employee ? 'My advances' : 'Advances',
          selected: location == '/advances',
          onTap: () => go('/advances'),
        ),
      if (!kIsWeb && isAdmin)
        _DrawerItem(
          icon: PhosphorIcons.buildings(),
          selectedIcon: PhosphorIcons.buildings(PhosphorIconsStyle.fill),
          accent: AppColors.darkBlue,
          label: 'Companies',
          selected: location == '/admin' || location.startsWith('/admin/companies'),
          onTap: () => go('/admin'),
        ),
      // A collection `if` covers one element only -- People needs its own Admin check
      // (it was showing for every role).
      if (!kIsWeb && isAdmin)
        _DrawerItem(
          icon: PhosphorIcons.users(),
          selectedIcon: PhosphorIcons.users(PhosphorIconsStyle.fill),
          accent: AppColors.darkBlue,
          label: 'People',
          selected: location == '/admin/people' || location.startsWith('/admin/people/'),
          onTap: () => go('/admin/people'),
        ),
      if (!kIsWeb && isHod && !employeeAdvances)
        _DrawerItem(
          icon: PhosphorIcons.money(),
          selectedIcon: PhosphorIcons.money(PhosphorIconsStyle.fill),
          accent: AppColors.orange,
          label: 'Funds',
          selected: location == '/topups' || location == '/funds',
          onTap: () => go('/topups'),
        ),
      if (!kIsWeb && (((isAccountant || isFinanceManager) && !employeeAdvances) || isAdmin))
        _DrawerItem(
          icon: PhosphorIcons.handCoins(),
          selectedIcon: PhosphorIcons.handCoins(PhosphorIconsStyle.fill),
          accent: AppColors.success,
          label: 'Top-ups',
          selected: location == '/topups',
          onTap: () => go('/topups'),
        ),
      _DrawerItem(
        icon: PhosphorIcons.bell(),
        selectedIcon: PhosphorIcons.bell(PhosphorIconsStyle.fill),
        accent: AppColors.orange,
        label: 'Alerts',
        selected: location == '/notifications',
        badgeCount: unreadCount,
        onTap: () => navigateGuarded(ref, () {
          Navigator.of(context).pop();
          context.push('/notifications');
        }),
      ),
      _DrawerItem(
        icon: PhosphorIcons.userCircle(),
        selectedIcon: PhosphorIcons.userCircle(PhosphorIconsStyle.fill),
        accent: AppColors.darkBlue,
        label: 'Profile',
        selected: location == '/profile',
        onTap: () => go('/profile'),
      ),
    ];

    return Drawer(
      backgroundColor: AppColors.background,
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.fromLTRB(20, 22, 20, 18),
              decoration: const BoxDecoration(
                color: AppColors.card,
                border: Border(bottom: BorderSide(color: AppColors.divider)),
              ),
              child: RegionLogo(
                regionCode: user?.regionCode,
                height: 44,
                width: double.infinity,
                alignment: Alignment.centerLeft,
              ),
            ),
            if ((user?.allowedRegions.length ?? 0) > 1)
              _CompanySwitcher(
                current: user!.regionCode,
                options: user.allowedRegions,
              ),
            if (!isAdmin) const _PettyCashLeft(),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(12, 16, 12, 12),
                children: [for (final item in items) item],
              ),
            ),
            Container(
              padding: const EdgeInsets.fromLTRB(12, 10, 12, 14),
              decoration: const BoxDecoration(
                border: Border(top: BorderSide(color: AppColors.divider)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (user != null) _WorkInfoCard(department: user.departmentName, regionCode: user.regionCode),
                  _DrawerItem(
                    icon: PhosphorIcons.signOut(),
                    selectedIcon: PhosphorIcons.signOut(PhosphorIconsStyle.fill),
                    accent: AppColors.danger,
                    label: 'Sign out',
                    selected: false,
                    onTap: () async {
                      Navigator.of(context).pop();
                      await ref.read(authControllerProvider.notifier).logout();
                      if (context.mounted) context.go('/login');
                    },
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

/// Department and company (of the region the user is working in), side by side just
/// above Sign out. The company name comes from the same branding lookup as the logo.
class _WorkInfoCard extends ConsumerWidget {
  const _WorkInfoCard({required this.department, required this.regionCode});

  final String? department;
  final String? regionCode;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final code = (regionCode ?? '').trim();
    final branding = code.isEmpty ? null : ref.watch(regionBrandingProvider(code)).valueOrNull;
    final company = (branding?.companyName ?? '').trim().isNotEmpty
        ? branding!.companyName!.trim()
        : (code.isEmpty ? '' : companyLabel(code));
    final dept = (department ?? '').trim();
    if (dept.isEmpty && company.isEmpty) return const SizedBox.shrink();

    Widget column(IconData icon, String value) => Expanded(
          child: Row(
            children: [
              PhosphorIcon(icon, size: 16, color: AppColors.darkBlue),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  value.isEmpty ? '—' : value,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 13.5,
                    height: 1.25,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
              ),
            ],
          ),
        );

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Container(
        padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.divider),
        ),
        child: IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              column(PhosphorIcons.usersThree(), dept),
              const VerticalDivider(width: 20, thickness: 1, color: AppColors.divider),
              column(PhosphorIcons.buildings(), company),
            ],
          ),
        ),
      ),
    );
  }
}

const _companyLabels = {'DUBAI': 'Dubai', 'UAE': 'UAE', 'KSA': 'KSA', 'OMAN': 'Oman'};

String companyLabel(String code) => _companyLabels[code.toUpperCase()] ?? code;

/// Shown only for users assigned to more than one company. Switching re-issues the
/// session, so every screen reloads its data for the new company.
class _CompanySwitcher extends ConsumerStatefulWidget {
  const _CompanySwitcher({required this.current, required this.options});

  final String? current;
  final List<String> options;

  @override
  ConsumerState<_CompanySwitcher> createState() => _CompanySwitcherState();
}

class _CompanySwitcherState extends ConsumerState<_CompanySwitcher> {
  bool _busy = false;

  Future<void> _switch(String code) async {
    if (code == widget.current || _busy) return;
    setState(() => _busy = true);
    try {
      await ref.read(authControllerProvider.notifier).switchRegion(code);
      if (!mounted) return;
      final role = UserRoleX.fromJson(ref.read(authControllerProvider).user?.role);
      Navigator.of(context).pop();
      context.go(homeRouteFor(role));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Couldn't switch region: $e")),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _openPicker() async {
    final picked = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      backgroundColor: AppColors.card,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (sheetContext) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Switch region',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
              ),
              const SizedBox(height: 4),
              const Text(
                'Your claims, petty cash and approvals reload for the region you pick.',
                style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
              ),
              const SizedBox(height: 12),
              for (final code in widget.options)
                _RegionOption(
                  code: code,
                  selected: code == widget.current,
                  onTap: () => Navigator.of(sheetContext).pop(code),
                ),
            ],
          ),
        ),
      ),
    );
    if (picked != null && mounted) navigateGuarded(ref, () => _switch(picked));
  }

  @override
  Widget build(BuildContext context) {
    final current = widget.current;
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: Material(
        color: AppColors.lightBlue,
        borderRadius: BorderRadius.circular(14),
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: _busy ? null : _openPicker,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(10, 10, 14, 10),
            child: Row(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: AppColors.card,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: PhosphorIcon(PhosphorIcons.globeHemisphereEast(), size: 22, color: AppColors.darkBlue),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text(
                        'REGION',
                        style: TextStyle(
                          fontSize: 11,
                          letterSpacing: 0.8,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        current == null ? 'Select region' : companyLabel(current),
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.darkBlue),
                      ),
                    ],
                  ),
                ),
                if (_busy)
                  const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                else
                  PhosphorIcon(PhosphorIcons.caretUpDown(), size: 20, color: AppColors.darkBlue),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _RegionOption extends StatelessWidget {
  const _RegionOption({required this.code, required this.selected, required this.onTap});

  final String code;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: selected ? AppColors.lightBlue : AppColors.background,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: onTap,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: selected ? AppColors.brightBlue : AppColors.divider),
            ),
            child: Row(
              children: [
                PhosphorIcon(
                  PhosphorIcons.mapPin(),
                  size: 20,
                  color: selected ? AppColors.brightBlue : AppColors.textSecondary,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    companyLabel(code),
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                      color: selected ? AppColors.darkBlue : AppColors.textPrimary,
                    ),
                  ),
                ),
                if (selected) PhosphorIcon(PhosphorIcons.checkCircle(), size: 22, color: AppColors.brightBlue),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Petty cash for the company the user is signed in under (their own pot, else their
/// department's), plus -- for someone in Dubai and KSA -- their KSA petty cash too, so both
/// show without switching company. Hidden when nothing is set up.
class _PettyCashLeft extends ConsumerWidget {
  const _PettyCashLeft();

  /// "SAR 2,000.00 can use now" for an employee advance with a hard limit, else "… left".
  static String _amount(PettyCashFund f) => f.spendLimit != null
      ? '${formatMoney(f.currency, f.uncommitted < 0 ? 0 : f.uncommitted)} can use now'
      : '${formatMoney(f.currency, f.available)} left';

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    final region = (user?.regionCode ?? '').toUpperCase();
    final funds = ref.watch(myFundsProvider).valueOrNull ?? const <PettyCashFund>[];
    final ownAdvances = ref.watch(myPcaAdvancesProvider).valueOrNull ?? const <PettyCashFund>[];

    final cards = <(String, String)>[];
    if (user?.usesEmployeeAdvances ?? false) {
      // One advance per employee, for all their projects.
      final advance = ownAdvances.where((f) => (f.regionCode ?? '').toUpperCase() == region).firstOrNull;
      if (advance != null) cards.add(('Your petty cash', _amount(advance)));
    } else {
      PettyCashFund? fund;
      for (final f in funds) {
        if ((f.regionCode ?? '').toUpperCase() != region) continue;
        if (f.ownerType == 'employee') {
          fund = f;
          break;
        }
        fund ??= f;
      }
      if (fund != null) {
        final owner = fund.ownerType == 'employee'
            ? 'Your petty cash'
            : '${(fund.departmentName ?? 'Department').trim()} petty cash';
        cards.add((owner, '${formatMoney(fund.currency, fund.available)} left'));
      }
    }
    // Petty cash in the other companies they belong to (e.g. KSA while signed in under Dubai).
    final others = [
      for (final f in ownAdvances)
        if ((f.regionCode ?? '').toUpperCase() != region) f,
    ];
    if (others.isNotEmpty && cards.isNotEmpty) {
      cards[0] = ('${cards[0].$1} (${companyLabel(region)})', cards[0].$2);
    }
    for (final f in others) {
      cards.add(('Your petty cash (${companyLabel(f.regionCode ?? '')})', _amount(f)));
    }
    if (cards.isEmpty) return const SizedBox.shrink();
    return Column(
      children: [for (final (title, amount) in cards) _PettyCashCard(title: title, amount: amount)],
    );
  }
}

class _PettyCashCard extends StatelessWidget {
  const _PettyCashCard({required this.title, required this.amount});

  final String title;
  final String amount;

  @override
  Widget build(BuildContext context) {
    final owner = title;
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 12),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.divider)),
      ),
      child: Container(
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
        decoration: BoxDecoration(
          color: AppColors.lightBlue,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                PhosphorIcon(PhosphorIcons.wallet(), size: 16, color: AppColors.darkBlue),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    owner,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.darkBlue),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              amount,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppColors.darkBlue),
            ),
          ],
        ),
      ),
    );
  }
}

class _DrawerItem extends StatelessWidget {
  const _DrawerItem({
    required this.icon,
    required this.selectedIcon,
    required this.accent,
    required this.label,
    required this.selected,
    required this.onTap,
    this.badgeCount = 0,
  });

  final PhosphorIconData icon;
  final PhosphorIconData selectedIcon;
  final Color accent;
  final String label;
  final bool selected;
  final VoidCallback onTap;
  final int badgeCount;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Material(
        color: selected ? AppColors.lightBlue : Colors.transparent,
        borderRadius: BorderRadius.circular(14),
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
            child: Row(
              children: [
                Badge(
                  isLabelVisible: badgeCount > 0,
                  backgroundColor: AppColors.orange,
                  label: Text(
                    badgeCount > 99 ? '99+' : '$badgeCount',
                    style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w700),
                  ),
                  child: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: accent.withValues(alpha: selected ? 0.18 : 0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: PhosphorIcon(selected ? selectedIcon : icon, color: accent, size: 20),
                  ),
                ),
                const SizedBox(width: 16),
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 15.5,
                    color: selected ? AppColors.darkBlue : AppColors.textPrimary,
                    fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

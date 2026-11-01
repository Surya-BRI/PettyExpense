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
      if (!kIsWeb && isAdmin)
        _DrawerItem(
          icon: PhosphorIcons.buildings(),
          selectedIcon: PhosphorIcons.buildings(PhosphorIconsStyle.fill),
          accent: AppColors.darkBlue,
          label: 'Companies',
          selected: location == '/admin' || location.startsWith('/admin/companies'),
          onTap: () => go('/admin'),
        ),
        _DrawerItem(
          icon: PhosphorIcons.users(),
          selectedIcon: PhosphorIcons.users(PhosphorIconsStyle.fill),
          accent: AppColors.darkBlue,
          label: 'People',
          selected: location == '/admin/people' || location.startsWith('/admin/people/'),
          onTap: () => go('/admin/people'),
        ),
      if (!kIsWeb && isHod)
        _DrawerItem(
          icon: PhosphorIcons.money(),
          selectedIcon: PhosphorIcons.money(PhosphorIconsStyle.fill),
          accent: AppColors.orange,
          label: 'Funds',
          selected: location == '/topups' || location == '/funds',
          onTap: () => go('/topups'),
        ),
      if (!kIsWeb && (isAccountant || isFinanceManager))
        _DrawerItem(
          icon: PhosphorIcons.arrowClockwise(),
          selectedIcon: PhosphorIcons.arrowClockwise(PhosphorIconsStyle.fill),
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
              child: _DrawerItem(
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
            ),
          ],
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
        SnackBar(content: Text("Couldn't switch company: $e")),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 12),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.divider)),
      ),
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: 'Company',
          prefixIcon: PhosphorIcon(PhosphorIcons.buildings(), size: 20),
          suffixIcon: _busy
              ? const Padding(
                  padding: EdgeInsets.all(12),
                  child: SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
                )
              : null,
        ),
        child: DropdownButtonHideUnderline(
          child: DropdownButton<String>(
            value: widget.options.contains(widget.current) ? widget.current : null,
            isExpanded: true,
            isDense: true,
            items: [
              for (final code in widget.options)
                DropdownMenuItem(value: code, child: Text(companyLabel(code))),
            ],
            onChanged: _busy
                ? null
                : (code) {
                    if (code != null) navigateGuarded(ref, () => _switch(code));
                  },
          ),
        ),
      ),
    );
  }
}

/// Petty cash left for the company the user is signed in under: their own pot if they
/// have one, otherwise their department's. Hidden when no pot is set up.
class _PettyCashLeft extends ConsumerWidget {
  const _PettyCashLeft();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final region = (ref.watch(authControllerProvider).user?.regionCode ?? '').toUpperCase();
    final funds = ref.watch(myFundsProvider).valueOrNull ?? const <PettyCashFund>[];
    PettyCashFund? fund;
    for (final f in funds) {
      if ((f.regionCode ?? '').toUpperCase() != region) continue;
      if (f.ownerType == 'employee') {
        fund = f;
        break;
      }
      fund ??= f;
    }
    if (fund == null) return const SizedBox.shrink();

    final owner = fund.ownerType == 'employee'
        ? 'Your petty cash'
        : '${(fund.departmentName ?? 'Department').trim()} petty cash';
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
              '${formatMoney(fund.currency, fund.available)} left',
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppColors.darkBlue),
            ),
            const SizedBox(height: 2),
            Text(
              'of ${formatMoney(fund.currency, fund.approvedLimit)} limit',
              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
            if (fund.pendingBills > 0) ...[
              const SizedBox(height: 6),
              Text(
                '${formatMoney(fund.currency, fund.pendingBills)} awaiting approval\n'
                '${formatMoney(fund.currency, fund.uncommitted)} free for new bills',
                style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
            ],
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

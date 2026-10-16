import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';

import '../api/enums.dart';
import '../features/authentication/auth_controller.dart';
import '../features/claims/confirm_claim_screen.dart' show navigateGuarded;
import '../features/notifications/notifications_screen.dart';
import '../routing/role_routes.dart';
import '../theme/app_theme.dart';

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
      if (isApprover) ...[
        _DrawerItem(
          icon: PhosphorIcons.house(),
          selectedIcon: PhosphorIcons.house(PhosphorIconsStyle.fill),
          accent: AppColors.darkBlue,
          label: 'Home',
          selected: location == homeRouteFor(role),
          onTap: () => go(homeRouteFor(role)),
        ),
        _DrawerItem(
          icon: PhosphorIcons.wallet(),
          selectedIcon: PhosphorIcons.wallet(PhosphorIconsStyle.fill),
          accent: AppColors.darkBlue,
          label: 'Claims',
          selected: location.startsWith('/approvals'),
          onTap: () => go('/approvals/${defaultStageFor(role)}'),
        ),
      ] else
        _DrawerItem(
          icon: PhosphorIcons.receipt(),
          selectedIcon: PhosphorIcons.receipt(PhosphorIconsStyle.fill),
          accent: AppColors.darkBlue,
          label: 'Claims',
          selected: location == '/claims' || location.startsWith('/claim/'),
          onTap: () => go('/claims'),
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
              child: Image(
                image: AssetImage(_regionLogoAsset(user?.regionCode)),
                width: double.infinity,
                height: 44,
                alignment: Alignment.centerLeft,
                fit: BoxFit.contain,
              ),
            ),
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

// Per-legal-entity branding (see ERP_SUBSIDIARY_TO_REGION_CODE in backend/auth/security.py
// for how a user's region_code is derived). OMAN/IN have no dedicated logo yet, so they
// fall back to the generic Blue Rhine Industries mark.
const _defaultRegionLogoAsset = 'assets/logos/Dubai_LOGO.png';
const _regionLogoAssets = {
  'UAE': 'assets/logos/UAE_LOGO.png',
  'KSA': 'assets/logos/KSA_LOGO.png',
};

String _regionLogoAsset(String? regionCode) => _regionLogoAssets[regionCode] ?? _defaultRegionLogoAsset;

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

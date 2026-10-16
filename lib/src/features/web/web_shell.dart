import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';

import '../../api/enums.dart';
import '../../routing/role_routes.dart';
import '../../theme/app_theme.dart';
import '../authentication/auth_controller.dart';
import '../claims/confirm_claim_screen.dart' show navigateGuarded;
import '../notifications/notifications_screen.dart';

/// Screens at or above this width get the sidebar layout instead of the bottom nav.
const double kWebShellBreakpoint = 1000;

/// Paths that are built for full width (tables, dashboard grids). Everything else
/// is a mobile-first screen and gets centered at a readable width instead of stretching.
const _fullWidthPaths = {'/dashboard', '/all-claims'};

/// Desktop/web layout: a fixed sidebar plus the routed page. Same brand colors,
/// type, and screens as the mobile app -- only the navigation chrome differs.
class WebShell extends ConsumerWidget {
  const WebShell({super.key, required this.location, required this.child});

  final String location;
  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final fullWidth = _fullWidthPaths.contains(location);

    return Scaffold(
      backgroundColor: AppColors.background,
      body: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _Sidebar(location: location),
          Expanded(
            child: fullWidth
                ? child
                : Align(
                    alignment: Alignment.topCenter,
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 880),
                      child: child,
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}

class _Sidebar extends ConsumerWidget {
  const _Sidebar({required this.location});

  final String location;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    final role = UserRoleX.fromJson(user?.role);
    final unread = ref.watch(unreadNotificationCountProvider).maybeWhen(data: (n) => n, orElse: () => 0);

    final items = <_NavEntry>[
      _NavEntry(PhosphorIcons.squaresFour(), PhosphorIcons.squaresFour(PhosphorIconsStyle.fill), 'Dashboard', '/dashboard'),
      _NavEntry(PhosphorIcons.table(), PhosphorIcons.table(PhosphorIconsStyle.fill), role.isApprover ? 'All claims' : 'My claims', '/all-claims'),
      if (role.isApprover)
        _NavEntry(PhosphorIcons.clipboardText(), PhosphorIcons.clipboardText(PhosphorIconsStyle.fill), 'My approval queue',
            '/approvals/${defaultStageFor(role)}', matchPrefix: '/approvals'),
      _NavEntry(PhosphorIcons.bell(), PhosphorIcons.bell(PhosphorIconsStyle.fill), 'Alerts', '/notifications', badge: unread),
      _NavEntry(PhosphorIcons.userCircle(), PhosphorIcons.userCircle(PhosphorIconsStyle.fill), 'Profile', '/profile'),
    ];

    return Container(
      width: 248,
      decoration: const BoxDecoration(
        color: AppColors.card,
        border: Border(right: BorderSide(color: AppColors.divider)),
      ),
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 22, 20, 6),
              child: Image.asset(
                'assets/brand/Br_fulllogo.png',
                height: 44,
                alignment: Alignment.centerLeft,
                fit: BoxFit.contain,
                errorBuilder: (_, _, _) => Image.asset('assets/brand/logo_blue_rhine.png', height: 44),
              ),
            ),
            const Padding(
              padding: EdgeInsets.fromLTRB(20, 4, 20, 20),
              child: Text(
                'Petty Cash and Expense Tracker',
                style: TextStyle(fontSize: 12, color: AppColors.textSecondary, fontWeight: FontWeight.w600),
              ),
            ),
            for (final item in items)
              _SidebarTile(
                entry: item,
                selected: item.matches(location),
                onTap: () => navigateGuarded(ref, () => context.go(item.path)),
              ),
            const Spacer(),
            if (!role.isApprover)
              const Padding(
                padding: EdgeInsets.fromLTRB(20, 0, 20, 12),
                child: Text(
                  'Scan new receipts from the mobile app.',
                  style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                ),
              ),
            const Divider(height: 1),
            _UserFooter(
              name: user?.displayName ?? '',
              detail: [_roleLabel(role), if (user?.regionCode != null) user!.regionCode!].join(' · '),
              logoAsset: _regionLogoAsset(user?.regionCode),
              onSignOut: () => ref.read(authControllerProvider.notifier).logout(),
            ),
          ],
        ),
      ),
    );
  }

  static String _roleLabel(UserRole role) => switch (role) {
        UserRole.employee => 'Employee',
        UserRole.hod => 'Head of Department',
        UserRole.accountant => 'Accountant',
        UserRole.financeManager => 'Finance Manager',
        UserRole.admin => 'Admin',
      };
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

class _NavEntry {
  const _NavEntry(this.icon, this.selectedIcon, this.label, this.path, {this.badge = 0, this.matchPrefix});

  final IconData icon;
  final IconData selectedIcon;
  final String label;
  final String path;
  final int badge;
  final String? matchPrefix;

  bool matches(String location) {
    if (matchPrefix != null) return location.startsWith(matchPrefix!);
    if (path == '/all-claims') return location == path || location.startsWith('/claim/');
    return location == path;
  }
}

class _SidebarTile extends StatelessWidget {
  const _SidebarTile({required this.entry, required this.selected, required this.onTap});

  final _NavEntry entry;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final color = selected ? AppColors.darkBlue : AppColors.textSecondary;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
      child: Material(
        color: selected ? AppColors.lightBlue : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
            child: Row(
              children: [
                Badge(
                  isLabelVisible: entry.badge > 0,
                  backgroundColor: AppColors.orange,
                  label: Text(
                    entry.badge > 99 ? '99+' : '${entry.badge}',
                    style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w700),
                  ),
                  child: Icon(selected ? entry.selectedIcon : entry.icon, color: color, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    entry.label,
                    style: TextStyle(
                      color: selected ? AppColors.darkBlue : AppColors.textPrimary,
                      fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                    ),
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

class _UserFooter extends StatelessWidget {
  const _UserFooter({required this.name, required this.detail, required this.logoAsset, required this.onSignOut});

  final String name;
  final String detail;
  final String logoAsset;
  final VoidCallback onSignOut;

  @override
  Widget build(BuildContext context) {
    final initial = name.trim().isEmpty ? 'U' : name.trim()[0].toUpperCase();
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 8, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 18,
                backgroundColor: AppColors.darkBlue,
                child: Text(initial, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(name, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w700)),
                    Text(detail, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                  ],
                ),
              ),
              IconButton(
                tooltip: 'Sign out',
                onPressed: onSignOut,
                icon: Icon(PhosphorIcons.signOut(), color: AppColors.textSecondary),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Padding(
            padding: const EdgeInsets.only(left: 2),
            child: Image.asset(logoAsset, height: 36, fit: BoxFit.contain, alignment: Alignment.centerLeft),
          ),
        ],
      ),
    );
  }
}

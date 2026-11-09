import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/enums.dart';
import '../../routing/role_routes.dart';
import '../admin/admin_hub_screen.dart';
import '../authentication/auth_controller.dart';
import '../claims/capture_receipt_sheet.dart';
import '../claims/confirm_claim_screen.dart' show navigateGuarded;
import '../notifications/notifications_screen.dart';
import '../../theme/app_theme.dart';
import '../web/web_shell.dart';

/// Universal bottom nav on every screen (except login). Buttons depend on role.
class MainShell extends ConsumerWidget {
  const MainShell({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Read here, outside the LayoutBuilder callback -- go_router's state lookup is only
    // reliable from this widget's own build.
    final location = GoRouterState.of(context).uri.path;
    // Wide screens (the web build on a desktop browser) get the sidebar layout instead.
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= kWebShellBreakpoint) {
          return WebShell(location: location, child: child);
        }
        return _buildMobile(context, ref, location);
      },
    );
  }

  Widget _buildMobile(BuildContext context, WidgetRef ref, String location) {
    final user = ref.watch(authControllerProvider).user;
    final role = UserRoleX.fromJson(user?.role);
    final isApprover = role.isApprover;
    final isAdmin = role == UserRole.admin;
    final homeSelected = location == '/dashboard';
    final adminSelected = location == '/admin' || location.startsWith('/admin/companies');
    final peopleSelected = location == '/admin/people' || location.startsWith('/admin/people/');
    final showApproverTopups =
        role == UserRole.hod || role == UserRole.financeManager || role == UserRole.accountant;
    // Professional Signs: the money tab is employee advances, not department top-ups.
    final employeeAdvances = user?.usesEmployeeAdvances ?? false;
    final topupsSelected = location == '/topups' || location == '/funds' || location == '/advances';
    final claimsSelected =
        location == '/claims' ||
        location == '/all-claims' ||
        location == '/confirm' ||
        location.startsWith('/claim/');
    final approvalsSelected = location.startsWith('/approvals') && location != '/approvals/history';
    final historySelected = location == '/approvals/history';
    final profileSelected = location == '/profile';
    final alertsSelected = location == '/notifications';
    final unreadCount = ref
        .watch(unreadNotificationCountProvider)
        .maybeWhen(data: (n) => n, orElse: () => 0);
    final strayAdminQueue = isAdmin && location.startsWith('/approvals');
    if (strayAdminQueue) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (context.mounted &&
            GoRouterState.of(context).uri.path.startsWith('/approvals')) {
          context.go('/admin');
        }
      });
    }

    return Scaffold(
      body: strayAdminQueue ? const AdminHubScreen() : child,
      bottomNavigationBar: BottomAppBar(
        color: AppColors.card,
        elevation: 8,
        height: 64,
        padding: EdgeInsets.zero,
        child: isAdmin
            ? Row(
                children: [
                  Expanded(
                    child: _NavItem(
                      icon: PhosphorIcons.buildings(),
                      selectedIcon: PhosphorIcons.buildings(PhosphorIconsStyle.fill),
                      label: 'Companies',
                      selected: adminSelected,
                      onTap: () => context.go('/admin'),
                    ),
                  ),
                  Expanded(
                    child: _NavItem(
                      icon: PhosphorIcons.users(),
                      selectedIcon: PhosphorIcons.users(PhosphorIconsStyle.fill),
                      label: 'People',
                      selected: peopleSelected,
                      onTap: () => context.go('/admin/people'),
                    ),
                  ),
                  Expanded(
                    child: _NavItem(
                      icon: PhosphorIcons.bell(),
                      selectedIcon: PhosphorIcons.bell(PhosphorIconsStyle.fill),
                      label: 'Alerts',
                      selected: alertsSelected,
                      badgeCount: unreadCount,
                      onTap: () => context.push('/notifications'),
                    ),
                  ),
                  Expanded(
                    child: _NavItem(
                      icon: PhosphorIcons.userCircle(),
                      selectedIcon: PhosphorIcons.userCircle(PhosphorIconsStyle.fill),
                      label: 'Profile',
                      selected: profileSelected,
                      onTap: () => context.go('/profile'),
                    ),
                  ),
                ],
              )
            : isApprover
            ? Row(
                children: [
                  if (kIsWeb)
                    Expanded(
                      child: _NavItem(
                        icon: PhosphorIcons.house(),
                        selectedIcon: PhosphorIcons.house(PhosphorIconsStyle.fill),
                        label: 'Home',
                        selected: homeSelected,
                        onTap: () => context.go(homeRouteFor(role)),
                      ),
                    ),
                  Expanded(
                    child: _NavItem(
                      icon: PhosphorIcons.wallet(),
                      selectedIcon: PhosphorIcons.wallet(PhosphorIconsStyle.fill),
                      label: 'Claims',
                      selected: approvalsSelected,
                      onTap: () =>
                          context.go('/approvals/${defaultStageFor(role)}'),
                    ),
                  ),
                  Expanded(
                    child: _NavItem(
                      icon: PhosphorIcons.clockClockwise(),
                      selectedIcon: PhosphorIcons.clockClockwise(PhosphorIconsStyle.fill),
                      label: 'History',
                      selected: historySelected,
                      onTap: () => context.go('/approvals/history'),
                    ),
                  ),
                  if (showApproverTopups)
                    Expanded(
                      child: _NavItem(
                        icon: role == UserRole.hod ? PhosphorIcons.money() : PhosphorIcons.handCoins(),
                        selectedIcon: role == UserRole.hod
                            ? PhosphorIcons.money(PhosphorIconsStyle.fill)
                            : PhosphorIcons.handCoins(PhosphorIconsStyle.fill),
                        label: employeeAdvances
                            ? 'Advances'
                            : role == UserRole.hod
                                ? 'Funds'
                                : 'Top-ups',
                        selected: topupsSelected,
                        onTap: () => context.go(employeeAdvances ? '/advances' : '/topups'),
                      ),
                    ),
                  Expanded(
                    child: _NavItem(
                      icon: PhosphorIcons.bell(),
                      selectedIcon: PhosphorIcons.bell(PhosphorIconsStyle.fill),
                      label: 'Alerts',
                      selected: alertsSelected,
                      badgeCount: unreadCount,
                      onTap: () => context.push('/notifications'),
                    ),
                  ),
                  Expanded(
                    child: _NavItem(
                      icon: PhosphorIcons.userCircle(),
                      selectedIcon: PhosphorIcons.userCircle(PhosphorIconsStyle.fill),
                      label: 'Profile',
                      selected: profileSelected,
                      onTap: () => context.go('/profile'),
                    ),
                  ),
                ],
              )
            : Row(
                children: [
                  // On native mobile, an employee's Home route IS /claims, so showing both
                  // would be two buttons for the same screen -- only web (whose Home is
                  // /dashboard) needs the separate button.
                  if (kIsWeb)
                    Expanded(
                      child: _NavItem(
                        icon: PhosphorIcons.house(),
                        selectedIcon: PhosphorIcons.house(PhosphorIconsStyle.fill),
                        label: 'Home',
                        selected: homeSelected,
                        onTap: () => navigateGuarded(
                          ref,
                          () => context.go(homeRouteFor(role)),
                        ),
                      ),
                    ),
                  Expanded(
                    child: _NavItem(
                      icon: PhosphorIcons.receipt(),
                      selectedIcon: PhosphorIcons.receipt(PhosphorIconsStyle.fill),
                      label: 'Claims',
                      selected: claimsSelected,
                      onTap: () =>
                          navigateGuarded(ref, () => context.go('/claims')),
                    ),
                  ),
                  // Capture relies on dart:io files, so scanning stays a mobile-app action.
                  if (!kIsWeb)
                    Expanded(
                      child: _NavItem(
                        icon: PhosphorIcons.camera(),
                        selectedIcon: PhosphorIcons.camera(PhosphorIconsStyle.fill),
                        label: 'Scan',
                        selected: false,
                        customIcon: const _ScanIcon(),
                        onTap: () => navigateGuarded(
                          ref,
                          () => showCaptureReceiptSheet(context, ref),
                        ),
                      ),
                    ),
                  Expanded(
                    child: _NavItem(
                      icon: PhosphorIcons.bell(),
                      selectedIcon: PhosphorIcons.bell(PhosphorIconsStyle.fill),
                      label: 'Alerts',
                      selected: alertsSelected,
                      badgeCount: unreadCount,
                      onTap: () =>
                          navigateGuarded(ref, () => context.push('/notifications')),
                    ),
                  ),
                  Expanded(
                    child: _NavItem(
                      icon: PhosphorIcons.userCircle(),
                      selectedIcon: PhosphorIcons.userCircle(PhosphorIconsStyle.fill),
                      label: 'Profile',
                      selected: profileSelected,
                      onTap: () =>
                          navigateGuarded(ref, () => context.go('/profile')),
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  const _NavItem({
    required this.icon,
    required this.selectedIcon,
    required this.label,
    required this.selected,
    required this.onTap,
    this.badgeCount = 0,
    this.customIcon,
  });

  final IconData icon;
  final IconData selectedIcon;
  final String label;
  final bool selected;
  final VoidCallback onTap;
  final int badgeCount;
  // Replaces the plain Icon entirely -- used for the gradient viewfinder on Scan.
  final Widget? customIcon;

  @override
  Widget build(BuildContext context) {
    final color = selected ? AppColors.darkBlue : AppColors.textSecondary;
    final iconWidget =
        customIcon ??
        Icon(selected ? selectedIcon : icon, color: color, size: 22);
    // Every item gets the same fixed height + Center wrapper so all five sit at
    // exactly the same vertical level in the row, regardless of icon/label differences.
    return InkWell(
      onTap: onTap,
      child: SizedBox(
        height: 64,
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Active state gets a filled pill behind the icon, not just a color swap,
              // so it reads at a glance instead of blending into the row.
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
                decoration: BoxDecoration(
                  color: selected ? AppColors.lightBlue : Colors.transparent,
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Badge(
                  isLabelVisible: badgeCount > 0,
                  backgroundColor: AppColors.orange,
                  label: Text(
                    badgeCount > 99 ? '99+' : '$badgeCount',
                    style: const TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  child: iconWidget,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                label,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                  color: color,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// A real camera glyph, gradient-tinted orange-to-blue for a more distinctive look
// than a flat single-color icon, while staying clearly recognizable as a camera.
class _ScanIcon extends StatelessWidget {
  const _ScanIcon();

  @override
  Widget build(BuildContext context) {
    return ShaderMask(
      shaderCallback: (bounds) => const LinearGradient(
        colors: [AppColors.orange, AppColors.darkBlue],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ).createShader(bounds),
      child: Icon(PhosphorIcons.camera(PhosphorIconsStyle.fill), size: 28, color: Colors.white),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/enums.dart';
import '../../routing/role_routes.dart';
import '../authentication/auth_controller.dart';
import '../claims/capture_receipt_sheet.dart';
import '../notifications/notifications_screen.dart';
import '../../theme/app_theme.dart';

/// Universal bottom nav on every screen (except login). Buttons depend on role.
class MainShell extends ConsumerWidget {
  const MainShell({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    final role = UserRoleX.fromJson(user?.role);
    final isApprover = role.isApprover;
    final location = GoRouterState.of(context).uri.path;

    final claimsSelected = location == '/claims' || location == '/confirm' || location.startsWith('/claim/');
    final approvalsSelected = location.startsWith('/approvals');
    final profileSelected = location == '/profile';
    final alertsSelected = location == '/notifications';
    final unreadCount = ref.watch(unreadNotificationCountProvider).maybeWhen(data: (n) => n, orElse: () => 0);

    return Scaffold(
      body: child,
      bottomNavigationBar: BottomAppBar(
        color: AppColors.card,
        elevation: 8,
        height: 64,
        padding: EdgeInsets.zero,
        child: isApprover
            ? Row(
                children: [
                  Expanded(
                    child: _NavItem(
                      icon: Icons.home_outlined,
                      selectedIcon: Icons.home,
                      label: 'Home',
                      selected: approvalsSelected,
                      onTap: () => context.go(homeRouteFor(role)),
                    ),
                  ),
                  Expanded(
                    child: _NavItem(
                      icon: Icons.account_balance_wallet_outlined,
                      selectedIcon: Icons.account_balance_wallet,
                      label: 'Claims',
                      selected: approvalsSelected,
                      onTap: () => context.go(homeRouteFor(role)),
                    ),
                  ),
                  Expanded(
                    child: _NavItem(
                      icon: Icons.notifications_outlined,
                      selectedIcon: Icons.notifications,
                      label: 'Alerts',
                      selected: alertsSelected,
                      badgeCount: unreadCount,
                      onTap: () => context.push('/notifications'),
                    ),
                  ),
                  Expanded(
                    child: _NavItem(
                      icon: Icons.person_outline,
                      selectedIcon: Icons.person,
                      label: 'Profile',
                      selected: profileSelected,
                      onTap: () => context.go('/profile'),
                    ),
                  ),
                ],
              )
            : Row(
                children: [
                  Expanded(
                    child: _NavItem(
                      icon: Icons.home_outlined,
                      selectedIcon: Icons.home,
                      label: 'Home',
                      selected: claimsSelected,
                      onTap: () => context.go('/claims'),
                    ),
                  ),
                  Expanded(
                    child: _NavItem(
                      icon: Icons.receipt_long_outlined,
                      selectedIcon: Icons.receipt_long,
                      label: 'Claims',
                      selected: claimsSelected,
                      onTap: () => context.go('/claims'),
                    ),
                  ),
                  Expanded(
                    child: _NavItem(
                      icon: Icons.photo_camera_outlined,
                      selectedIcon: Icons.photo_camera,
                      label: 'Scan',
                      selected: false,
                      customIcon: const _ScanIcon(),
                      onTap: () => showCaptureReceiptSheet(context, ref),
                    ),
                  ),
                  Expanded(
                    child: _NavItem(
                      icon: Icons.notifications_outlined,
                      selectedIcon: Icons.notifications,
                      label: 'Alerts',
                      selected: alertsSelected,
                      badgeCount: unreadCount,
                      onTap: () => context.push('/notifications'),
                    ),
                  ),
                  Expanded(
                    child: _NavItem(
                      icon: Icons.person_outline,
                      selectedIcon: Icons.person,
                      label: 'Profile',
                      selected: profileSelected,
                      onTap: () => context.go('/profile'),
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
    final iconWidget = customIcon ?? Icon(selected ? selectedIcon : icon, color: color, size: 24);
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
              Badge(
                isLabelVisible: badgeCount > 0,
                backgroundColor: AppColors.orange,
                label: Text(
                  badgeCount > 99 ? '99+' : '$badgeCount',
                  style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w700),
                ),
                child: iconWidget,
              ),
              const SizedBox(height: 2),
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
      child: const Icon(Icons.photo_camera, size: 28, color: Colors.white),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/enums.dart';
import '../../routing/role_routes.dart';
import '../authentication/auth_controller.dart';
import '../claims/capture_receipt_sheet.dart';
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

    final claimsSelected = location == '/claims' || location.startsWith('/claim/');
    final approvalsSelected = location.startsWith('/approvals');
    final profileSelected = location == '/profile';

    return Scaffold(
      body: child,
      floatingActionButton: isApprover
          ? null
          : FloatingActionButton(
              onPressed: () => showCaptureReceiptSheet(context, ref),
              backgroundColor: AppColors.orange,
              foregroundColor: Colors.white,
              elevation: 4,
              child: const Icon(Icons.photo_camera_outlined, size: 28),
            ),
      floatingActionButtonLocation: isApprover
          ? null
          : FloatingActionButtonLocation.centerDocked,
      bottomNavigationBar: BottomAppBar(
        color: AppColors.card,
        elevation: 8,
        shape: isApprover ? null : const CircularNotchedRectangle(),
        notchMargin: 8,
        height: 64,
        padding: EdgeInsets.zero,
        child: isApprover
            ? Row(
                children: [
                  Expanded(
                    child: _NavItem(
                      icon: Icons.account_balance_wallet_outlined,
                      selectedIcon: Icons.account_balance_wallet,
                      label: 'Approvals',
                      selected: approvalsSelected,
                      onTap: () => context.go(homeRouteFor(role)),
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
                      icon: Icons.receipt_long_outlined,
                      selectedIcon: Icons.receipt_long,
                      label: 'My claims',
                      selected: claimsSelected || location == '/confirm',
                      onTap: () => context.go('/claims'),
                    ),
                  ),
                  const SizedBox(width: 72),
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
  });

  final IconData icon;
  final IconData selectedIcon;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final color = selected ? AppColors.darkBlue : AppColors.textSecondary;
    return InkWell(
      onTap: onTap,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(selected ? selectedIcon : icon, color: color, size: 24),
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
    );
  }
}

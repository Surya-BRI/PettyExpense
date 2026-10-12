import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../widgets/brand_app_bar.dart';
import '../authentication/auth_controller.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  String _initials(AuthUser? user) {
    final name = (user?.displayName ?? user?.username ?? 'U').trim();
    final parts = name.split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    if (parts.isEmpty) return 'U';
    if (parts.length == 1) {
      return parts.first.substring(0, parts.first.length >= 2 ? 2 : 1).toUpperCase();
    }
    return ('${parts[0][0]}${parts[1][0]}').toUpperCase();
  }

  String _roleLabel(String? role) {
    switch ((role ?? '').toLowerCase()) {
      case 'finance_manager':
        return 'Finance Manager';
      case 'accountant':
        return 'Accountant';
      case 'hod':
        return 'Head of Department';
      case 'admin':
        return 'Admin';
      case 'employee':
        return 'Employee';
      default:
        return role?.isNotEmpty == true ? role! : 'User';
    }
  }

  static const _sectionLabelStyle = TextStyle(
    color: AppColors.textSecondary,
    fontWeight: FontWeight.w700,
    fontSize: 13,
    letterSpacing: 0.2,
  );

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final user = auth.user;
    final role = _roleLabel(user?.role);

    return Scaffold(
      backgroundColor: AppColors.background,
      // Every role has a dedicated Alerts tab in the bottom nav now, so the app-bar bell is redundant here.
      appBar: const BrandAppBar(title: 'Profile', showNotificationAction: false),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
        children: [
          const Text(
            'My Profile',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: AppColors.textPrimary),
          ),
          const SizedBox(height: 4),
          const Text(
            'View your account information',
            style: TextStyle(fontSize: 13.5, color: AppColors.textSecondary),
          ),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.fromLTRB(20, 22, 20, 22),
            decoration: BoxDecoration(
              color: AppColors.card,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.divider),
              boxShadow: [
                BoxShadow(
                  color: AppColors.darkBlue.withValues(alpha: 0.06),
                  blurRadius: 16,
                  offset: const Offset(0, 6),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Stack(
                      clipBehavior: Clip.none,
                      children: [
                        Container(
                          width: 72,
                          height: 72,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: [
                                AppColors.lightBlue,
                                AppColors.darkBlue.withValues(alpha: 0.18),
                              ],
                            ),
                            border: Border.all(color: AppColors.darkBlue, width: 2),
                          ),
                          alignment: Alignment.center,
                          child: Text(
                            _initials(user),
                            style: const TextStyle(
                              fontSize: 24,
                              fontWeight: FontWeight.w800,
                              color: AppColors.darkBlue,
                            ),
                          ),
                        ),
                        Positioned(
                          right: -2,
                          bottom: -2,
                          child: Container(
                            width: 24,
                            height: 24,
                            decoration: BoxDecoration(
                              color: AppColors.card,
                              shape: BoxShape.circle,
                              border: Border.all(color: AppColors.divider),
                            ),
                            padding: const EdgeInsets.all(3),
                            child: Image.asset(
                              'assets/brand/logo_br_mark.png',
                              fit: BoxFit.contain,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            user?.displayName ?? 'Guest',
                            style: const TextStyle(
                              fontSize: 19,
                              fontWeight: FontWeight.w800,
                              color: AppColors.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 3),
                          Text(
                            role,
                            style: const TextStyle(fontSize: 14, color: AppColors.textSecondary),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    if (user?.regionCode != null)
                      _InfoChip(
                        label: user!.regionCode!,
                        background: AppColors.orange.withValues(alpha: 0.12),
                        foreground: AppColors.orange,
                      ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 26),
          const Text('Contact Information', style: _sectionLabelStyle),
          const SizedBox(height: 10),
          _InfoRowCard(
            icon: Icons.person_outline,
            iconColor: AppColors.darkBlue,
            label: 'Username',
            value: user?.username ?? '—',
          ),
          const SizedBox(height: 10),
          _InfoRowCard(
            icon: Icons.badge_outlined,
            iconColor: AppColors.orange,
            label: 'Role',
            value: role,
          ),
          const SizedBox(height: 10),
          _InfoRowCard(
            icon: Icons.location_on_outlined,
            iconColor: AppColors.orange,
            label: 'Region',
            value: user?.regionCode ?? '—',
          ),
          const SizedBox(height: 26),
          const Text('Account', style: _sectionLabelStyle),
          const SizedBox(height: 10),
          _ActionCard(
            icon: Icons.logout_rounded,
            title: 'Sign out',
            subtitle: 'Return to the sign-in screen',
            iconColor: AppColors.orange,
            onTap: () async {
              await ref.read(authControllerProvider.notifier).logout();
              if (context.mounted) context.go('/login');
            },
          ),
          const SizedBox(height: 24),
          Center(
            child: Text(
              'Blue Rhine · Expense claims',
              style: TextStyle(
                color: AppColors.textSecondary.withValues(alpha: 0.85),
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  const _InfoChip({
    required this.label,
    required this.background,
    required this.foreground,
  });

  final String label;
  final Color background;
  final Color foreground;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: foreground,
          fontWeight: FontWeight.w700,
          fontSize: 12,
        ),
      ),
    );
  }
}

/// A labelled value row used under "Contact Information" -- icon chip on the left,
/// small muted label above a bold value on the right.
class _InfoRowCard extends StatelessWidget {
  const _InfoRowCard({
    required this.icon,
    required this.iconColor,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final Color iconColor;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.divider),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: iconColor.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: iconColor),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12.5)),
                const SizedBox(height: 3),
                Text(
                  value,
                  style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.textPrimary, fontSize: 15),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}


class _ActionCard extends StatelessWidget {
  const _ActionCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.iconColor,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final Color iconColor;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.divider),
          ),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: iconColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: iconColor),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        color: AppColors.textPrimary,
                        fontSize: 15,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      subtitle,
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12.5,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: AppColors.textSecondary),
            ],
          ),
        ),
      ),
    );
  }
}

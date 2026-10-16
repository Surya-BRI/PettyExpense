import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';

import '../features/claims/confirm_claim_screen.dart' show navigateGuarded;
import '../features/notifications/notifications_screen.dart';
import '../theme/app_theme.dart';

/// Bell icon for AppBars; badge shows notification count.
class NotificationBellButton extends ConsumerWidget {
  const NotificationBellButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(unreadNotificationCountProvider);
    final count = async.maybeWhen(data: (n) => n, orElse: () => 0);

    return IconButton(
      tooltip: 'Notifications',
      onPressed: () => navigateGuarded(ref, () => context.push('/notifications')),
      icon: Badge(
        isLabelVisible: count > 0,
        backgroundColor: AppColors.orange,
        label: Text(
          count > 99 ? '99+' : '$count',
          style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700),
        ),
        child: Icon(PhosphorIcons.bell()),
      ),
    );
  }
}

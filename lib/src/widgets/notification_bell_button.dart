import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/notifications/notifications_screen.dart';
import '../theme/app_theme.dart';

/// Bell icon for AppBars; badge shows notification count.
class NotificationBellButton extends ConsumerWidget {
  const NotificationBellButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(notificationsProvider);
    final count = async.maybeWhen(data: (items) => items.length, orElse: () => 0);

    return IconButton(
      tooltip: 'Notifications',
      onPressed: () => context.push('/notifications'),
      icon: Badge(
        isLabelVisible: count > 0,
        backgroundColor: AppColors.orange,
        label: Text(
          count > 99 ? '99+' : '$count',
          style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700),
        ),
        child: const Icon(Icons.notifications_outlined),
      ),
    );
  }
}

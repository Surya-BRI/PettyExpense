import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../api/api_client.dart';
import '../../api/enums.dart';
import '../../routing/role_routes.dart';
import '../../theme/app_theme.dart';
import '../../widgets/brand_app_bar.dart';
import '../authentication/auth_controller.dart';

class AppNotification {
  const AppNotification({
    required this.id,
    required this.title,
    required this.body,
    required this.createdAt,
    required this.kind,
    required this.unread,
    this.route,
  });

  final int id;
  final String title;
  final String body;
  final DateTime? createdAt;
  final String kind; // submitted | approved | rejected | paid | info
  final bool unread;
  final String? route;
}

const _titleByType = {
  'submission': 'New claim to review',
  'approval': 'Claim approved',
  'rejection': 'Claim rejected',
  'dispute': 'Claim disputed — correction needed',
  'paid': 'Claim paid',
  'test': 'Test notification',
};

const _kindByType = {
  'submission': 'submitted',
  'approval': 'approved',
  'rejection': 'rejected',
  'dispute': 'rejected',
  'paid': 'paid',
};

// Backend stores "subject\n\nbody" as one message column; split it back apart for display.
String _bodyOf(String message) {
  final parts = message.split('\n\n');
  return parts.length > 1 ? parts.sublist(1).join('\n\n') : message;
}

String? _routeFor(Map<String, dynamic> row, UserRole role) {
  final txnId = row['transaction_id'];
  if (txnId == null) return null;
  final type = row['type'] as String?;
  final claimStatus = row['claim_status'] as String?;
  final isFinalApproval = type == 'approval' && claimStatus == 'approved';
  final approverFacing = type == 'submission' || (type == 'approval' && !isFinalApproval);
  if (approverFacing) {
    final stage = (row['current_stage'] as String?) ?? defaultStageFor(role);
    return '/approvals/$stage/$txnId';
  }
  if (type == 'test') return null;
  return '/claim/$txnId';
}

final notificationsProvider = FutureProvider.autoDispose<List<AppNotification>>((ref) async {
  final auth = ref.watch(authControllerProvider);
  final api = ref.watch(apiClientProvider);
  final role = UserRoleX.fromJson(auth.user?.role);

  final rows = await api.notifications(limit: 50);
  return rows.map((row) {
    final type = row['type'] as String? ?? 'test';
    final message = row['message'] as String? ?? '';
    return AppNotification(
      id: row['id'] as int,
      title: _titleByType[type] ?? 'Notification',
      body: _bodyOf(message),
      createdAt: _parseDate(row['sent_at'] as String?),
      kind: _kindByType[type] ?? 'info',
      unread: row['status'] != 'read',
      route: _routeFor(row, role),
    );
  }).toList();
});

final unreadNotificationCountProvider = FutureProvider.autoDispose<int>((ref) async {
  final api = ref.watch(apiClientProvider);
  return api.unreadNotificationCount();
});

DateTime? _parseDate(String? raw) {
  if (raw == null || raw.isEmpty) return null;
  return DateTime.tryParse(raw);
}

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(notificationsProvider);
    final finance = UserRoleX.fromJson(ref.watch(authControllerProvider).user?.role).isApprover;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: BrandAppBar(
        title: 'Notifications',
        automaticallyImplyLeading: true,
        showNotificationAction: false,
        actions: [
          IconButton(
            tooltip: 'Mark all read',
            onPressed: () async {
              await ref.read(apiClientProvider).markAllNotificationsRead();
              ref.invalidate(notificationsProvider);
              ref.invalidate(unreadNotificationCountProvider);
            },
            icon: const Icon(Icons.done_all),
          ),
          IconButton(
            tooltip: 'Refresh',
            onPressed: () => ref.invalidate(notificationsProvider),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text('$e', textAlign: TextAlign.center),
          ),
        ),
        data: (items) {
          if (items.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 72,
                      height: 72,
                      decoration: const BoxDecoration(
                        color: AppColors.lightBlue,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(
                        Icons.notifications_none_rounded,
                        size: 36,
                        color: AppColors.darkBlue,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      finance ? 'No claims waiting for review' : 'No notifications yet',
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 16,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      finance
                          ? 'New salesman submissions will show up here.'
                          : 'Updates on your claims will appear here.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: AppColors.textSecondary),
                    ),
                  ],
                ),
              ),
            );
          }

          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
            itemCount: items.length,
            separatorBuilder: (context, index) => const SizedBox(height: 10),
            itemBuilder: (context, i) {
              final n = items[i];
              return Material(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(14),
                child: InkWell(
                  borderRadius: BorderRadius.circular(14),
                  onTap: () async {
                    if (n.unread) {
                      await ref.read(apiClientProvider).markNotificationRead(n.id);
                      ref.invalidate(unreadNotificationCountProvider);
                    }
                    if (n.route != null) context.push(n.route!);
                  },
                  child: Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: n.unread ? AppColors.darkBlue : AppColors.divider),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: _kindBg(n.kind),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Icon(_kindIcon(n.kind), color: _kindFg(n.kind), size: 22),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                n.title,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w700,
                                  color: AppColors.textPrimary,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                n.body,
                                style: const TextStyle(
                                  color: AppColors.textSecondary,
                                  fontSize: 13,
                                ),
                              ),
                              if (n.createdAt != null) ...[
                                const SizedBox(height: 6),
                                Text(
                                  DateFormat('dd MMM yyyy, HH:mm').format(n.createdAt!.toLocal()),
                                  style: const TextStyle(
                                    color: AppColors.textSecondary,
                                    fontSize: 11,
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                        const Icon(Icons.chevron_right, color: AppColors.textSecondary),
                      ],
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }

  IconData _kindIcon(String kind) {
    switch (kind) {
      case 'approved':
        return Icons.check_circle_outline;
      case 'rejected':
        return Icons.cancel_outlined;
      case 'paid':
        return Icons.payments_outlined;
      default:
        return Icons.receipt_long_outlined;
    }
  }

  Color _kindFg(String kind) {
    switch (kind) {
      case 'approved':
        return AppColors.success;
      case 'rejected':
        return AppColors.danger;
      case 'paid':
        return AppColors.darkBlue;
      default:
        return AppColors.orange;
    }
  }

  Color _kindBg(String kind) => _kindFg(kind).withValues(alpha: 0.12);
}

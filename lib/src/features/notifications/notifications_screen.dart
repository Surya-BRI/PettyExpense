import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../api/api_client.dart';
import '../../api/enums.dart';
import '../../api/models.dart';
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
    this.route,
  });

  final String id;
  final String title;
  final String body;
  final DateTime? createdAt;
  final String kind; // submitted | approved | rejected | paid | info
  final String? route;
}

final notificationsProvider = FutureProvider.autoDispose<List<AppNotification>>((ref) async {
  final auth = ref.watch(authControllerProvider);
  final api = ref.watch(apiClientProvider);
  final role = UserRoleX.fromJson(auth.user?.role);
  final approver = role.isApprover;

  final List<ExpenseClaim> claims;
  if (approver) {
    claims = await api.approvalsQueue(defaultStageFor(role));
  } else {
    claims = await api.myClaims();
  }

  final items = <AppNotification>[];
  for (final c in claims) {
    final when = _parseDate(c.updatedAt) ??
        _parseDate(c.decidedAt) ??
        _parseDate(c.submittedAt) ??
        _parseDate(c.createdAt);

    if (approver) {
      items.add(
        AppNotification(
          id: 'sub-${c.id}',
          title: c.status == 'disputed' ? 'Disputed claim resubmitted' : 'New claim to review',
          body: '${c.vendor} · ₹${c.amount.toStringAsFixed(2)} · ${c.category}',
          createdAt: when,
          kind: 'submitted',
          route: '/approvals/${c.currentStage ?? defaultStageFor(role)}/${c.id}',
        ),
      );
    } else {
      final notification = switch (c.status) {
        'submitted' => AppNotification(
            id: 'mine-sub-${c.id}',
            title: 'Claim submitted',
            body: '${c.vendor} is waiting for approval (${c.currentStage ?? '-'})',
            createdAt: when,
            kind: 'submitted',
            route: '/claim/${c.id}',
          ),
        'disputed' => AppNotification(
            id: 'mine-disp-${c.id}',
            title: 'Claim disputed — correction needed',
            body: c.remarks?.isNotEmpty == true ? c.remarks! : '${c.vendor} was sent back for correction',
            createdAt: when,
            kind: 'rejected',
            route: '/claim/${c.id}',
          ),
        'approved' => AppNotification(
            id: 'mine-ap-${c.id}',
            title: 'Claim approved',
            body: '${c.vendor} was approved',
            createdAt: when,
            kind: 'approved',
            route: '/claim/${c.id}',
          ),
        'rejected' => AppNotification(
            id: 'mine-re-${c.id}',
            title: 'Claim rejected',
            body: c.remarks?.isNotEmpty == true ? c.remarks! : '${c.vendor} was rejected',
            createdAt: when,
            kind: 'rejected',
            route: '/claim/${c.id}',
          ),
        'paid' => AppNotification(
            id: 'mine-pd-${c.id}',
            title: 'Claim paid',
            body: '${c.vendor} · ₹${c.amount.toStringAsFixed(2)} marked as paid',
            createdAt: when,
            kind: 'paid',
            route: '/claim/${c.id}',
          ),
        _ => null,
      };
      if (notification != null) items.add(notification);
    }
  }

  items.sort((a, b) {
    final ad = a.createdAt ?? DateTime.fromMillisecondsSinceEpoch(0);
    final bd = b.createdAt ?? DateTime.fromMillisecondsSinceEpoch(0);
    return bd.compareTo(ad);
  });
  return items;
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
                  onTap: n.route == null ? null : () => context.push(n.route!),
                  child: Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppColors.divider),
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

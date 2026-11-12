import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/enums.dart';
import '../api/models.dart';
import '../features/approvals/approval_detail_screen.dart';
import '../features/approvals/approval_queue_screen.dart';
import '../features/approvals/approver_history_screen.dart';
import '../features/authentication/auth_controller.dart';
import '../features/authentication/login_screen.dart';
import '../features/claims/claim_detail_screen.dart';
import '../features/claims/bill_line_mode.dart';
import '../features/claims/confirm_claim_screen.dart';
import '../features/claims/my_claims_screen.dart';
import '../features/home/main_shell.dart';
import '../features/notifications/notifications_screen.dart';
import '../features/admin/admin_company_screen.dart';
import '../features/admin/admin_hub_screen.dart';
import '../features/admin/admin_people_screen.dart';
import '../features/admin/my_funds_screen.dart';
import '../features/admin/topups_screen.dart';
import '../features/payments/payments_screen.dart';
import '../features/pca/advances_screen.dart';
import '../features/pca/site_pca_screen.dart';
import '../features/profile/profile_screen.dart';
import '../features/web/all_claims_screen.dart';
import '../features/web/dashboard_screen.dart';
import 'role_routes.dart';

/// Notifies go_router when auth changes (without recreating the router).
class _AuthRefresh extends ChangeNotifier {
  _AuthRefresh(this.ref) {
    ref.listen<AuthState>(authControllerProvider, (_, __) => notifyListeners());
  }

  final Ref ref;
}

final appRouterProvider = Provider<GoRouter>((ref) {
  final refresh = _AuthRefresh(ref);
  ref.onDispose(refresh.dispose);

  return GoRouter(
    initialLocation: kIsWeb ? '/dashboard' : '/claims',
    refreshListenable: refresh,
    redirect: (context, state) {
      final auth = ref.read(authControllerProvider);
      final loc = state.uri.path;
      final role = UserRoleX.fromJson(auth.user?.role);
      final approver = role.isApprover;
      // No session → login. Do not keep the main shell with a fake Guest user
      // while tokens are restoring after restart / hot reload / logout.
      if (auth.user == null) {
        return loc == '/login' ? null : '/login';
      }

      if (loc == '/login') {
        return homeRouteFor(role);
      }

      if (loc == '/') {
        return homeRouteFor(role);
      }

      // Approvers review queues, not a personal "My claims" / capture flow.
      if (approver && (loc == '/claims' || loc == '/confirm')) {
        return homeRouteFor(role);
      }

      // Admin screens are Admin-only.
      if (loc.startsWith('/admin') && role != UserRole.admin) {
        return homeRouteFor(role);
      }

      // Admin is organisation setup, not an approver queue (a single claim opened from
      // Payments is fine).
      if (!kIsWeb &&
          role == UserRole.admin &&
          loc.startsWith('/approvals') &&
          !RegExp(r'^/approvals/[a-z_]+/\d+$').hasMatch(loc)) {
        return '/admin';
      }

      // Recording reimbursement payments is the Finance Manager's (Professional Signs: Accounts
      // Manager's) and Admin's job.
      final employeeAdvances = auth.user?.usesEmployeeAdvances ?? false;
      final canPay = role == UserRole.financeManager || role == UserRole.admin;
      if (loc == '/payments' && !canPay) {
        return homeRouteFor(role);
      }

      // Employee-advance company: no department pots or department top-ups, only advances.
      if (employeeAdvances && role != UserRole.admin && (loc == '/funds' || loc == '/topups')) {
        return '/advances';
      }
      // Site-pot company (Blue Rhine Contracting): only site petty cash.
      if ((auth.user?.usesSitePots ?? false) &&
          role != UserRole.admin &&
          (loc == '/funds' || loc == '/topups' || loc == '/advances')) {
        return '/site-pca';
      }

      // Dashboard and all-claims are web-only screens; redirect mobile employees away.
      if (!kIsWeb && !approver && (loc == '/dashboard' || loc == '/all-claims')) {
        return '/claims';
      }

      // Employees do not manage pots — leftover cash is shown on the bill, not a Funds tab.
      if (role == UserRole.employee && loc == '/funds') {
        return '/claims';
      }
      // HOD remaining + top-ups live on one screen.
      if (role == UserRole.hod && loc == '/funds') {
        return '/topups';
      }

      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(
            path: '/dashboard',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: DashboardScreen(),
            ),
          ),
          GoRoute(
            path: '/all-claims',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: AllClaimsScreen(),
            ),
          ),
          GoRoute(
            path: '/claims',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: MyClaimsScreen(),
            ),
          ),
          GoRoute(
            path: '/profile',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: ProfileScreen(),
            ),
          ),
          GoRoute(
            path: '/admin',
            builder: (context, state) => const AdminHubScreen(),
          ),
          GoRoute(
            path: '/admin/companies/:id',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['id'] ?? '') ?? 0;
              return AdminCompanyScreen(regionId: id);
            },
          ),
          GoRoute(
            path: '/admin/regions',
            redirect: (context, state) => '/admin',
            builder: (context, state) => const AdminHubScreen(),
          ),
          GoRoute(
            path: '/admin/people',
            builder: (context, state) => const AdminPeopleScreen(),
            routes: [
              GoRoute(
                path: ':regionCode',
                builder: (context, state) {
                  final extra = state.extra;
                  return AdminCompanyPeopleScreen(
                    regionCode: state.pathParameters['regionCode'] ?? '',
                    region: extra is RegionConfig ? extra : null,
                  );
                },
                routes: [
                  GoRoute(
                    path: ':userId',
                    builder: (context, state) {
                      final extra = state.extra;
                      return AdminPersonScreen(
                        userId: int.tryParse(state.pathParameters['userId'] ?? '') ?? 0,
                        regionCode: state.pathParameters['regionCode'] ?? '',
                        user: extra is OrgUser ? extra : null,
                      );
                    },
                  ),
                ],
              ),
            ],
          ),
          GoRoute(
            path: '/admin/funds',
            redirect: (context, state) => '/admin',
            builder: (context, state) => const AdminHubScreen(),
          ),
          GoRoute(
            path: '/funds',
            builder: (context, state) => const MyFundsScreen(),
          ),
          GoRoute(
            path: '/topups',
            builder: (context, state) => const TopupsScreen(),
          ),
          GoRoute(
            path: '/payments',
            builder: (context, state) => const PaymentsScreen(),
          ),
          GoRoute(
            path: '/advances',
            builder: (context, state) => const AdvancesScreen(),
          ),
          GoRoute(
            path: '/site-pca',
            builder: (context, state) => const SitePcaScreen(),
          ),
          GoRoute(
            path: '/notifications',
            builder: (context, state) => const NotificationsScreen(),
          ),
          GoRoute(
            path: '/confirm',
            builder: (context, state) {
              final extra = state.extra;
              if (extra is Map) {
                return ConfirmClaimScreen(
                  ocr: extra['ocr'] as OcrResult,
                  localPaths: (extra['localPaths'] as List?)?.cast<String>() ?? const [],
                  runOcr: extra['runOcr'] == true,
                  lineMode: extra['lineMode'] as BillLineMode? ?? BillLineMode.single,
                  ocrMode: extra['ocrMode'] as String? ?? 'auto',
                );
              }
              return const Scaffold(
                body: Center(child: Text('Missing receipt data')),
              );
            },
          ),
          GoRoute(
            path: '/claim/:id',
            builder: (context, state) =>
                ClaimDetailScreen(claimId: int.parse(state.pathParameters['id']!)),
          ),
          GoRoute(
            path: '/claim/:id/edit',
            builder: (context, state) => ConfirmClaimScreen(
              existingClaimId: int.parse(state.pathParameters['id']!),
            ),
          ),
          GoRoute(
            path: '/approvals/history',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: ApproverHistoryScreen(),
            ),
          ),
          GoRoute(
            path: '/approvals/:stage',
            pageBuilder: (context, state) => NoTransitionPage(
              child: ApprovalQueueScreen(
                stage: state.pathParameters['stage']!,
                initialFilter: state.uri.queryParameters['filter'],
              ),
            ),
          ),
          GoRoute(
            path: '/approvals/:stage/:id',
            builder: (context, state) => ApprovalDetailScreen(
              stage: state.pathParameters['stage']!,
              transactionId: int.parse(state.pathParameters['id']!),
            ),
          ),
        ],
      ),
    ],
  );
});

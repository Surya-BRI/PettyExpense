import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../api/enums.dart';
import '../api/models.dart';
import '../features/approvals/approval_detail_screen.dart';
import '../features/approvals/approval_queue_screen.dart';
import '../features/authentication/auth_controller.dart';
import '../features/authentication/login_screen.dart';
import '../features/claims/claim_detail_screen.dart';
import '../features/claims/confirm_claim_screen.dart';
import '../features/claims/my_claims_screen.dart';
import '../features/home/main_shell.dart';
import '../features/notifications/notifications_screen.dart';
import '../features/profile/profile_screen.dart';
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
    initialLocation: '/claims',
    refreshListenable: refresh,
    redirect: (context, state) {
      final auth = ref.read(authControllerProvider);
      final loc = state.matchedLocation;
      final role = UserRoleX.fromJson(auth.user?.role);
      final approver = role.isApprover;
      final loggedOut = auth.user == null && !auth.useMockBypass && !auth.isLoading;

      if (loc == '/login') {
        if (auth.user != null && !auth.useMockBypass) {
          return homeRouteFor(role);
        }
        return null;
      }

      if (loggedOut) return '/login';

      if (loc == '/') {
        return homeRouteFor(role);
      }

      // Approvers review queues, not a personal "My claims" / capture flow.
      if (approver && (loc == '/claims' || loc == '/confirm')) {
        return homeRouteFor(role);
      }

      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
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
                  localPath: extra['localPath'] as String?,
                  runOcr: extra['runOcr'] == true,
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
            path: '/approvals/:stage',
            pageBuilder: (context, state) => NoTransitionPage(
              child: ApprovalQueueScreen(stage: state.pathParameters['stage']!),
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

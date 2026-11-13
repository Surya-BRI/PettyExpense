import 'package:expense_app/src/api/models.dart';
import 'package:expense_app/src/features/admin/my_funds_screen.dart' show myFundsProvider;
import 'package:expense_app/src/features/authentication/auth_controller.dart';
import 'package:expense_app/src/features/notifications/notifications_screen.dart'
    show unreadNotificationCountProvider;
import 'package:expense_app/src/widgets/app_nav_drawer.dart';
import 'package:expense_app/src/widgets/region_branding.dart' show regionBrandingProvider;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

/// Opens the side menu for a user with [role] and returns the visible menu labels.
Future<void> _openDrawerAs(WidgetTester tester, String role, {List<String> regions = const ['DUBAI']}) async {
  final scaffoldKey = GlobalKey<ScaffoldState>();
  final router = GoRouter(
    initialLocation: '/home',
    routes: [
      GoRoute(
        path: '/home',
        builder: (_, __) => Scaffold(key: scaffoldKey, drawer: const AppNavDrawer(), body: const SizedBox()),
      ),
    ],
  );
  final user = AuthUser(
    id: 1,
    displayName: 'Test',
    role: role,
    regionCode: regions.first,
    allowedRegions: regions,
  );
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith((ref) => AuthController.withState(AuthState(user: user))),
        unreadNotificationCountProvider.overrideWith((ref) async => 0),
        myFundsProvider.overrideWith((ref) async => const <PettyCashFund>[]),
        regionBrandingProvider.overrideWith((ref, code) async => null),
      ],
      child: MaterialApp.router(routerConfig: router),
    ),
  );
  scaffoldKey.currentState!.openDrawer();
  await tester.pumpAndSettle();
}

void main() {
  for (final role in ['employee', 'hod', 'accountant', 'finance_manager']) {
    testWidgets('$role does not see the Admin-only People / Companies entries', (tester) async {
      await _openDrawerAs(tester, role);
      expect(find.text('People'), findsNothing);
      expect(find.text('Companies'), findsNothing);
      expect(find.text('Profile'), findsOneWidget);
    });
  }

  testWidgets('admin sees People and Companies', (tester) async {
    await _openDrawerAs(tester, 'admin');
    expect(find.text('People'), findsOneWidget);
    expect(find.text('Companies'), findsOneWidget);
  });

  testWidgets('multi-region user gets the Region switcher, single-region does not', (tester) async {
    await _openDrawerAs(tester, 'employee', regions: const ['DUBAI', 'KSA']);
    expect(find.text('REGION'), findsOneWidget);
    // Region card + the company fallback in the department/company card at the bottom.
    expect(find.text('BRI UAE · Blue Rhine Industries'), findsWidgets); // DUBAI, by its ERP name
  });

  testWidgets('single-region user has no Region switcher', (tester) async {
    await _openDrawerAs(tester, 'employee');
    expect(find.text('REGION'), findsNothing);
  });
}

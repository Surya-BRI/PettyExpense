// Top-up chain on screen: Accounts verify or return (reason required), FM approves only once
// verified, a returned top-up shows why, every top-up shows its history, Admin can raise one.
import 'package:expense_app/src/api/api_client.dart';
import 'package:expense_app/src/api/models.dart';
import 'package:expense_app/src/features/admin/topups_screen.dart';
import 'package:expense_app/src/features/authentication/auth_controller.dart';
import 'package:expense_app/src/features/notifications/notifications_screen.dart'
    show unreadNotificationCountProvider;
import 'package:expense_app/src/widgets/region_branding.dart' show regionBrandingProvider;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

TopupRequest _topup(String status, {List<Map<String, dynamic>> history = const []}) => TopupRequest.fromJson({
      'id': 5,
      'amount': 1000.0,
      'status': status,
      'remarks': 'Month-end',
      'requester_name': 'Priya HOD',
      'department_name': 'Sales',
      'transaction_ids': [11, 12],
      'history': history,
    });

class _FakeApi extends ApiClient {
  _FakeApi() : super(baseUrl: 'http://fake');

  final List<String> calls = [];

  @override
  Future<TopupRequest> returnTopup(int id, {required String remarks}) async {
    calls.add('return:$id:$remarks');
    return _topup('returned');
  }

  @override
  Future<TopupRequest> verifyTopup(int id, {String? remarks}) async {
    calls.add('verify:$id');
    return _topup('verified');
  }
}

List<Override> _overrides(String role, _FakeApi api, {List<TopupRequest> topups = const []}) => [
      apiClientProvider.overrideWithValue(api),
      authControllerProvider.overrideWith(
        (ref) => AuthController.withState(
          AuthState(user: AuthUser(id: 1, displayName: 'Test', role: role, regionCode: 'DUBAI')),
        ),
      ),
      topupsProvider.overrideWith((ref) async => topups),
      unreadNotificationCountProvider.overrideWith((ref) async => 0),
      regionBrandingProvider.overrideWith((ref, code) async => null),
    ];

Future<_FakeApi> _tile(WidgetTester tester, String role, TopupRequest t) async {
  final api = _FakeApi();
  await tester.pumpWidget(ProviderScope(
    overrides: _overrides(role, api),
    child: MaterialApp(home: Scaffold(body: SingleChildScrollView(child: TopupRequestTile(request: t)))),
  ));
  await tester.pumpAndSettle();
  return api;
}

Finder _btn(String label) => find.ancestor(
      of: find.text(label),
      matching: find.byWidgetPredicate((w) => w is ButtonStyleButton),
    );

void main() {
  testWidgets('Accountant sees Verify and Return to HOD on a submitted top-up', (tester) async {
    await _tile(tester, 'accountant', _topup('submitted'));
    expect(_btn('Verify'), findsOneWidget);
    expect(_btn('Return to HOD'), findsOneWidget);
    expect(_btn('Approve'), findsNothing);
  });

  testWidgets('Return needs a reason and sends it', (tester) async {
    final api = await _tile(tester, 'accountant', _topup('submitted'));
    await tester.tap(_btn('Return to HOD'));
    await tester.pumpAndSettle();
    final confirm = tester.widget<FilledButton>(find.widgetWithText(FilledButton, 'Return'));
    expect(confirm.onPressed, isNull); // no reason yet
    await tester.enterText(find.byType(TextField), 'Receipt missing');
    await tester.pump();
    await tester.tap(find.widgetWithText(FilledButton, 'Return'));
    await tester.pumpAndSettle();
    expect(api.calls, ['return:5:Receipt missing']);
  });

  testWidgets('FM gets Approve only after Accounts verified', (tester) async {
    await _tile(tester, 'finance_manager', _topup('submitted'));
    expect(_btn('Approve'), findsNothing);
    expect(_btn('Verify'), findsNothing);
  });

  testWidgets('FM sees Approve and Reject once verified', (tester) async {
    await _tile(tester, 'finance_manager', _topup('verified'));
    expect(_btn('Approve'), findsOneWidget);
    expect(_btn('Reject'), findsOneWidget);
  });

  testWidgets('returned top-up shows the reason and its history', (tester) async {
    await _tile(
      tester,
      'hod',
      _topup('returned', history: [
        {'action': 'requested', 'actor_name': 'Priya HOD', 'comment': 'Month-end', 'at': '2026-11-01T09:00:00'},
        {'action': 'returned', 'actor_name': 'Ravi Accounts', 'comment': 'Receipt missing', 'at': '2026-11-01T11:00:00'},
      ]),
    );
    expect(find.textContaining('Returned to HOD'), findsWidgets);
    expect(find.textContaining('Returned: Receipt missing'), findsOneWidget);
    expect(find.text('History (2)'), findsOneWidget);
    await tester.tap(find.text('History (2)'));
    await tester.pumpAndSettle();
    expect(find.text('Requested · Priya HOD'), findsOneWidget);
    expect(find.text('Returned to HOD · Ravi Accounts'), findsOneWidget);
  });

  testWidgets('Admin gets a Request top-up button on the Top-ups screen', (tester) async {
    await tester.pumpWidget(ProviderScope(
      overrides: _overrides('admin', _FakeApi()),
      child: const MaterialApp(home: TopupsScreen()),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Request top-up'), findsOneWidget);
  });

  testWidgets('Accountant has no Request top-up button', (tester) async {
    await tester.pumpWidget(ProviderScope(
      overrides: _overrides('accountant', _FakeApi()),
      child: const MaterialApp(home: TopupsScreen()),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Request top-up'), findsNothing);
  });
}

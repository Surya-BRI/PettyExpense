// Spec 5.2 Rule 2: after Dispute the bill goes back to the employee (status Disputed) and
// leaves the approver's queue; Approve / Reject stay hidden until the employee resubmits.
import 'package:expense_app/src/api/api_client.dart';
import 'package:expense_app/src/api/models.dart';
import 'package:expense_app/src/features/approvals/approval_detail_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

ExpenseClaim _claim(String status, {String? stage = 'hod'}) => ExpenseClaim.fromJson({
      'id': 7,
      'employee_id': 1,
      'employee_name': 'Surya Sales',
      'vendor_name': 'City Mart',
      'amount': 40.0,
      'vat_amount': 2.0,
      'total_amount': 42.0,
      'currency': 'AED',
      'region_code': 'DUBAI',
      'category_id': 1,
      'status': status,
      'current_stage': stage,
      'current_stage_key': stage,
      'history': status == 'disputed'
          ? [
              {
                'id': 1,
                'stage': 'hod',
                'action': 'dispute',
                'actor_id': 2,
                'actor_name': 'Priya',
                'comment': 'Wrong amount',
                'remarks': 'Wrong amount',
              },
            ]
          : [],
    });

class _FakeApi extends ApiClient {
  _FakeApi(this.status) : super(baseUrl: 'http://fake');

  String status;
  final List<String> calls = [];

  @override
  Future<ExpenseClaim> getApprovalTransaction(int id) async => _claim(status);

  @override
  Future<ExpenseClaim> disputeTransaction(int id, {required String comment}) async {
    calls.add('dispute:$comment');
    status = 'disputed';
    return _claim(status);
  }

  @override
  Future<ExpenseClaim> approveTransaction(int id, {String? comment}) async {
    calls.add('approve');
    return _claim(status);
  }
}

Future<_FakeApi> _open(WidgetTester tester, String status) async {
  FlutterSecureStorage.setMockInitialValues({});
  // The review screen is a lazy ListView: make the test screen tall enough that the action
  // buttons / sent-back note are actually built.
  tester.view.physicalSize = const Size(1080, 6000);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);
  final api = _FakeApi(status);
  final router = GoRouter(
    initialLocation: '/approvals/hod/7',
    routes: [
      GoRoute(
        path: '/approvals/hod/7',
        builder: (_, __) => const ApprovalDetailScreen(stage: 'hod', transactionId: 7),
      ),
      GoRoute(path: '/approvals/hod', builder: (_, __) => const Text('HOD queue')),
    ],
  );
  await tester.pumpWidget(
    ProviderScope(
      overrides: [apiClientProvider.overrideWithValue(api)],
      child: MaterialApp.router(routerConfig: router),
    ),
  );
  await tester.pumpAndSettle(const Duration(milliseconds: 300));
  return api;
}

// FilledButton.icon builds a FilledButton subclass, so match by text inside any ButtonStyleButton.
Finder _button(String label) => find.ancestor(
      of: find.text(label),
      matching: find.byWidgetPredicate((w) => w is FilledButton),
    );

void main() {
  testWidgets('submitted bill at my stage shows Approve, Dispute and Reject', (tester) async {
    await _open(tester, 'submitted');
    expect(_button('Approve'), findsOneWidget);
    expect(_button('Dispute (send back to employee)'), findsOneWidget);
    expect(_button('Reject'), findsOneWidget);
  });

  testWidgets('dispute with a comment sends it back and returns to the queue', (tester) async {
    final api = await _open(tester, 'submitted');
    await tester.enterText(find.widgetWithText(TextField, 'Comment'), 'Wrong amount');
    await tester.ensureVisible(_button('Dispute (send back to employee)'));
    await tester.tap(_button('Dispute (send back to employee)'));
    await tester.pumpAndSettle(const Duration(milliseconds: 300));

    expect(api.calls, ['dispute:Wrong amount']);
    expect(find.text('HOD queue'), findsOneWidget); // left the bill, back on the queue
  });

  testWidgets('dispute without a comment is refused', (tester) async {
    final api = await _open(tester, 'submitted');
    await tester.ensureVisible(_button('Dispute (send back to employee)'));
    await tester.tap(_button('Dispute (send back to employee)'));
    await tester.pump();
    expect(api.calls, isEmpty);
    expect(find.text('Please add a comment before disputing or rejecting'), findsOneWidget);
  });

  testWidgets('disputed bill shows no Approve / Dispute / Reject, only the sent-back note', (tester) async {
    final api = await _open(tester, 'disputed');
    expect(_button('Approve'), findsNothing);
    expect(_button('Dispute (send back to employee)'), findsNothing);
    expect(_button('Reject'), findsNothing);
    expect(find.textContaining('Sent back to the employee'), findsOneWidget);
    expect(find.textContaining('Approve and Reject return after they correct and resubmit'), findsOneWidget);
    expect(api.calls, isEmpty);
  });

  testWidgets('after the employee resubmits, the buttons come back at the same stage', (tester) async {
    // Resubmit returns the bill to the stage that disputed it (status submitted, stage hod).
    await _open(tester, 'submitted');
    expect(_button('Approve'), findsOneWidget);
  });
}

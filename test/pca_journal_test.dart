// Professional Signs: at the Accounts step the approver must record the expense journal
// (EJV, or EJVB for a multi-branch transaction) and its ERP number before approving.
// Companies without a journal step approve as before.
import 'package:expense_app/src/api/api_client.dart';
import 'package:expense_app/src/api/models.dart';
import 'package:expense_app/src/features/approvals/approval_detail_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

ExpenseClaim _claim({String? journalStage}) => ExpenseClaim.fromJson({
      'id': 9,
      'employee_id': 1,
      'employee_name': 'Ahmed',
      'vendor_name': 'Saco',
      'amount': 100.0,
      'vat_amount': 15.0,
      'total_amount': 115.0,
      'currency': 'SAR',
      'region_code': 'KSA',
      'category_id': 1,
      'status': 'submitted',
      'type': 'petty_cash',
      'op_number': 'OP-2201',
      'current_stage': 'accountant',
      'current_stage_key': 'accountant',
      'journal_stage': journalStage,
      'stage_labels': {'accountant': 'Accounts (EJV)', 'finance_manager': 'Accounts Manager'},
      'history': [],
    });

class _FakeApi extends ApiClient {
  _FakeApi(this.journalStage) : super(baseUrl: 'http://fake');

  final String? journalStage;
  final List<String> calls = [];

  @override
  Future<ExpenseClaim> getApprovalTransaction(int id) async => _claim(journalStage: journalStage);

  @override
  Future<ExpenseClaim> approveTransaction(
    int id, {
    String? comment,
    String? journalType,
    String? journalReference,
  }) async {
    calls.add('approve:$journalType:$journalReference');
    return _claim(journalStage: journalStage);
  }
}

Future<_FakeApi> _open(WidgetTester tester, {String? journalStage}) async {
  FlutterSecureStorage.setMockInitialValues({});
  tester.view.physicalSize = const Size(1080, 6000);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);
  final api = _FakeApi(journalStage);
  final router = GoRouter(
    initialLocation: '/approvals/accountant/9',
    routes: [
      GoRoute(
        path: '/approvals/accountant/9',
        builder: (_, _) => const ApprovalDetailScreen(stage: 'accountant', transactionId: 9),
      ),
      GoRoute(path: '/approvals/accountant', builder: (_, _) => const Text('Accounts queue')),
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

FilledButton _approve(WidgetTester tester, String label) => tester.widget<FilledButton>(
      find.ancestor(of: find.text(label), matching: find.byWidgetPredicate((w) => w is FilledButton)),
    );

void main() {
  testWidgets('Accounts must record EJV/EJVB and its number before approving', (tester) async {
    final api = await _open(tester, journalStage: 'accountant');

    expect(find.text('Expense journal'), findsOneWidget);
    expect(_approve(tester, 'Approve (enter the journal above)').onPressed, isNull);

    await tester.tap(find.text('EJVB (multi-branch)'));
    await tester.pump();
    expect(_approve(tester, 'Approve (enter the journal above)').onPressed, isNull); // number still missing

    await tester.enterText(find.widgetWithText(TextField, 'Journal number *'), 'EJVB-2211');
    await tester.pump();
    final approve = _approve(tester, 'Approve');
    expect(approve.onPressed, isNotNull);

    await tester.ensureVisible(find.text('Approve'));
    await tester.tap(find.text('Approve'));
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    expect(api.calls, ['approve:EJVB:EJVB-2211']);
  });

  testWidgets('a company without a journal step approves as before', (tester) async {
    final api = await _open(tester);
    expect(find.text('Expense journal'), findsNothing);
    await tester.ensureVisible(find.text('Approve'));
    await tester.tap(find.text('Approve'));
    await tester.pumpAndSettle(const Duration(milliseconds: 300));
    expect(api.calls, ['approve:null:null']);
  });
}

import 'package:expense_app/src/api/api_client.dart';
import 'package:expense_app/src/api/models.dart';
import 'package:expense_app/src/features/claims/confirm_claim_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

/// Backend stand-in for editing a saved draft: getClaim seeds the form, updateDraft/submitClaim
/// record what was sent so the test can assert the two-call sequence and ordering.
class _FakeApi extends ApiClient {
  _FakeApi({this.submitShouldFail = false}) : super(baseUrl: 'http://fake');

  final bool submitShouldFail;
  Map<String, dynamic>? updatedBody;
  final List<String> calls = [];

  @override
  Future<ExpenseClaim> getClaim(int id) async => const ExpenseClaim(
        id: 42,
        employeeId: 1,
        amount: 45.0,
        vatAmount: 0,
        totalAmount: 45.0,
        currency: 'AED',
        categoryId: 1,
        status: 'draft',
        vendorName: 'Uber',
        billDate: '06/07/2026',
        billNumber: null, // the gap this whole feature exists to let the employee fill in
      );

  @override
  Future<List<CategoryRef>> categories() async =>
      const [CategoryRef(id: 1, name: 'First aid'), CategoryRef(id: 2, name: 'Stationery')];

  @override
  Future<List<ProjectRef>> projects() async => const [];

  @override
  Future<ExpenseClaim> updateDraft(int id, Map<String, dynamic> body) async {
    calls.add('updateDraft');
    updatedBody = body;
    return const ExpenseClaim(id: 42, employeeId: 1, amount: 45.0, currency: 'AED', categoryId: 1, status: 'draft');
  }

  @override
  Future<ExpenseClaim> submitClaim(int id) async {
    calls.add('submitClaim');
    if (submitShouldFail) {
      throw Exception('Finish these fields before submitting: bill number');
    }
    return const ExpenseClaim(id: 42, employeeId: 1, amount: 45.0, currency: 'AED', categoryId: 1, status: 'submitted');
  }
}

Future<_FakeApi> _pumpEditScreen(WidgetTester tester, {bool submitShouldFail = false}) async {
  FlutterSecureStorage.setMockInitialValues({});
  tester.view.physicalSize = const Size(1200, 8000);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  final api = _FakeApi(submitShouldFail: submitShouldFail);
  final router = GoRouter(
    routes: [
      GoRoute(path: '/', builder: (_, _) => const ConfirmClaimScreen(existingClaimId: 42)),
      GoRoute(path: '/claim/:id', builder: (_, s) => Text('claim ${s.pathParameters['id']}')),
    ],
  );
  await tester.pumpWidget(
    ProviderScope(
      overrides: [apiClientProvider.overrideWithValue(api)],
      child: MaterialApp.router(routerConfig: router),
    ),
  );
  await tester.pumpAndSettle(const Duration(milliseconds: 500));
  return api;
}

Finder _field(String label) => find.widgetWithText(TextField, label);

void main() {
  testWidgets('prefills vendor, amount and bill date from the existing claim', (tester) async {
    await _pumpEditScreen(tester);
    expect(find.text('Uber'), findsOneWidget);
    // Amount and total both seeded to 45.0 (vat 0) -- two fields legitimately show "45.00".
    expect(find.text('45.00'), findsNWidgets(2));
    expect(find.text('06/07/2026'), findsOneWidget);
  });

  testWidgets('shows what is still missing before it can be submitted', (tester) async {
    await _pumpEditScreen(tester);
    expect(find.textContaining('Bill number'), findsOneWidget);
  });

  testWidgets('saving a draft only calls updateDraft, not submitClaim', (tester) async {
    final api = await _pumpEditScreen(tester);
    await tester.tap(find.widgetWithText(OutlinedButton, 'Save as draft'));
    await tester.pumpAndSettle();
    expect(api.calls, ['updateDraft']);
    expect(find.text('claim 42'), findsOneWidget);
  });

  testWidgets('submit is blocked client-side while bill number is still blank', (tester) async {
    final api = await _pumpEditScreen(tester);
    await tester.tap(find.widgetWithText(FilledButton, 'Submit for approval'));
    await tester.pumpAndSettle();
    expect(api.calls, isEmpty);
    expect(find.textContaining('bill / invoice number'), findsOneWidget);
  });

  testWidgets('submit happy path calls updateDraft then submitClaim in order', (tester) async {
    final api = await _pumpEditScreen(tester);
    await tester.enterText(_field('Bill / invoice number *'), 'INV-1001');
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Submit for approval'));
    await tester.pumpAndSettle();
    // The in-app cross-check dialog appears before the real submit -- confirm it.
    final confirmButton = find.widgetWithText(FilledButton, 'Looks right, submit');
    if (confirmButton.evaluate().isNotEmpty) {
      await tester.tap(confirmButton);
      await tester.pumpAndSettle();
    }
    expect(api.calls, ['updateDraft', 'submitClaim']);
    expect(find.text('claim 42'), findsOneWidget);
  });

  testWidgets(
    'updateDraft success + submitClaim failure keeps the edit screen up with the error shown',
    (tester) async {
      await _pumpEditScreen(tester, submitShouldFail: true);
      await tester.enterText(_field('Bill / invoice number *'), 'INV-1001');
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(FilledButton, 'Submit for approval'));
      await tester.pumpAndSettle();
      final confirmButton = find.widgetWithText(FilledButton, 'Looks right, submit');
      if (confirmButton.evaluate().isNotEmpty) {
        await tester.tap(confirmButton);
        await tester.pumpAndSettle();
      }
      // Still on the edit screen -- not redirected to the (nonexistent, in this test) read-only
      // detail route -- with the submit error visible.
      expect(find.text('claim 42'), findsNothing);
      expect(find.textContaining('Finish these fields before submitting'), findsOneWidget);
    },
  );
}

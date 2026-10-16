import 'dart:io';

import 'package:expense_app/src/api/api_client.dart';
import 'package:expense_app/src/api/models.dart';
import 'package:expense_app/src/features/claims/bill_line_mode.dart';
import 'package:expense_app/src/features/claims/confirm_claim_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

/// Backend stand-in: OCR reads three item lines; createClaim records what was sent.
class _FakeApi extends ApiClient {
  _FakeApi() : super(baseUrl: 'http://fake');

  Map<String, dynamic>? createdBody;

  @override
  Future<OcrResult> analyzeReceipt(int receiptId, {String ocrMode = 'auto'}) async => const OcrResult(
        receiptId: 7,
        s3Key: 'k',
        vendor: 'Bab Al Hayat Pharmacy',
        currency: 'AED',
        date: '06/07/2026',
        totalAmount: 55.54,
        vatAmount: 0,
        ocrStatus: 'done',
        lineItems: [
          OcrLineItem(description: 'Gauze swab', quantity: 5, amount: 23.94),
          OcrLineItem(description: 'Cotton wool', quantity: 5, amount: 23.94),
          OcrLineItem(description: 'Scissor', quantity: 1, amount: 7.66),
        ],
      );

  @override
  Future<List<CategoryRef>> categories() async =>
      const [CategoryRef(id: 1, name: 'First aid'), CategoryRef(id: 2, name: 'Stationery')];

  @override
  Future<List<ProjectRef>> projects() async => const [];

  @override
  Future<ExpenseClaim> createClaim(Map<String, dynamic> body) async {
    createdBody = body;
    return const ExpenseClaim(id: 99, employeeId: 1, amount: 0, currency: 'AED', categoryId: 1, status: 'submitted');
  }
}

Future<_FakeApi> _pumpScreen(WidgetTester tester) async {
  FlutterSecureStorage.setMockInitialValues({});
  tester.view.physicalSize = const Size(1200, 8000);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  final api = _FakeApi();
  final router = GoRouter(
    routes: [
      GoRoute(
        path: '/',
        builder: (_, _) => const ConfirmClaimScreen(
          ocr: OcrResult(receiptId: 7, s3Key: 'k', vendor: '', date: '', ocrStatus: 'pending'),
          runOcr: true,
          lineMode: BillLineMode.multiple,
        ),
      ),
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

/// The scanned bill has no number and the screen requires one before it will submit or save.
Future<void> _enterBillNumber(WidgetTester tester) async {
  await tester.enterText(_field('Bill / invoice number *'), 'INV-1001');
  await tester.pumpAndSettle();
}

/// The editor shows one item card at a time; step forward to the n-th (1-based) item.
Future<void> _goToItem(WidgetTester tester, int n) async {
  for (var i = 1; i < n; i++) {
    await tester.tap(find.byTooltip('Next item'));
    await tester.pumpAndSettle();
  }
}

void main() {
  setUpAll(() => HttpOverrides.global = null);

  testWidgets('scanned item lines are editable and the totals are computed from them', (tester) async {
    await _pumpScreen(tester);

    expect(find.text('Items on this bill'), findsOneWidget);
    expect(find.text('3 items'), findsOneWidget);
    // One card at a time: item 1 is showing, the others are a tap away.
    expect(find.text('Item 1 of 3'), findsOneWidget);
    expect(find.text('Gauze swab'), findsOneWidget);
    expect(find.text('Scissor'), findsNothing);
    await _goToItem(tester, 3);
    expect(find.text('Item 3 of 3'), findsOneWidget);
    expect(find.text('Scissor'), findsOneWidget);
    expect(find.text('AED 55.54'), findsWidgets); // sum of items == printed total
    // No single-amount fields in multi mode -- the money comes from the lines.
    expect(find.textContaining('Amount excl. VAT (AED) *'), findsNothing);
    expect(find.text('Expense type *'), findsNothing);
  });

  testWidgets('submit asks for a cross-check, then sends the lines, line-derived totals and the main category', (tester) async {
    final api = await _pumpScreen(tester);

    await _enterBillNumber(tester);
    // Correct the scissor price (item 3).
    await _goToItem(tester, 3);
    await tester.enterText(find.widgetWithText(TextField, '7.66'), '10.00');
    await tester.pumpAndSettle();
    expect(find.text('AED 57.88'), findsWidgets);
    // Bill printed 55.54, items now 57.88: the mismatch is called out in a box.
    expect(find.textContaining('Items don’t match the bill'), findsOneWidget);
    expect(find.textContaining('difference AED 2.34'), findsOneWidget);

    await tester.tap(find.text('Submit for approval'));
    await tester.pumpAndSettle();

    // The cross-check box appears first and nothing is sent yet.
    expect(find.text('Please cross-check before submitting'), findsOneWidget);
    expect(find.textContaining('An item may be missing or misread'), findsOneWidget);
    expect(api.createdBody, isNull);

    await tester.tap(find.text('Looks right, submit'));
    await tester.pumpAndSettle();

    final body = api.createdBody!;
    expect(body['line_items'], [
      {'description': 'Gauze swab', 'quantity': 5.0, 'amount': 23.94, 'category_id': 1, 'op_number': null},
      {'description': 'Cotton wool', 'quantity': 5.0, 'amount': 23.94, 'category_id': 1, 'op_number': null},
      {'description': 'Scissor', 'quantity': 1.0, 'amount': 10.0, 'category_id': 1, 'op_number': null},
    ]);
    expect(body['total_amount'], 57.88);
    expect(body['amount'], 57.88);
    expect(body['category_id'], 1);
    expect(find.text('claim 99'), findsOneWidget);
  });

  testWidgets('going back from the cross-check box submits nothing', (tester) async {
    final api = await _pumpScreen(tester);
    await _enterBillNumber(tester);

    await tester.tap(find.text('Submit for approval'));
    await tester.pumpAndSettle();
    expect(find.text('Please cross-check before submitting'), findsOneWidget);
    // Items add up to the printed total here, so no warning box is shown.
    expect(find.textContaining('An item may be missing or misread'), findsNothing);

    await tester.tap(find.text('Go back and check'));
    await tester.pumpAndSettle();

    expect(api.createdBody, isNull);
    expect(find.text('Please cross-check before submitting'), findsNothing);
    expect(find.text('Submit for approval'), findsOneWidget);
  });

  testWidgets('saving a draft skips the cross-check box', (tester) async {
    final api = await _pumpScreen(tester);
    await _enterBillNumber(tester);

    await tester.tap(find.text('Save as draft'));
    await tester.pumpAndSettle();

    expect(find.text('Please cross-check before submitting'), findsNothing);
    expect(api.createdBody, isNotNull);
    expect(api.createdBody!['submit'], false);
  });

  testWidgets('an incomplete line blocks submit and says what is missing', (tester) async {
    final api = await _pumpScreen(tester);

    await tester.tap(find.text('Add item'));
    await tester.pumpAndSettle();
    expect(find.text('4 items'), findsOneWidget);
    expect(find.text('Item 4 of 4'), findsOneWidget); // adding jumps to the new item

    await tester.tap(find.text('Submit for approval'));
    await tester.pumpAndSettle();

    expect(api.createdBody, isNull);
    expect(find.text('Please cross-check before submitting'), findsNothing);
    expect(find.textContaining('Item 4: Add the item name'), findsOneWidget);
  });

  testWidgets('removing a line updates the total', (tester) async {
    await _pumpScreen(tester);
    await _goToItem(tester, 3);
    await tester.tap(find.byTooltip('Remove item'));
    await tester.pumpAndSettle();
    expect(find.text('2 items'), findsOneWidget);
    expect(find.text('Scissor'), findsNothing);
    expect(find.text('AED 47.88'), findsWidgets);
    // Removing the last item lands on the one before it.
    expect(find.text('Item 2 of 2'), findsOneWidget);
    expect(_field('Item *'), findsOneWidget);
  });
}

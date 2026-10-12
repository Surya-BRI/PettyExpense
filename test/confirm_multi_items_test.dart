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

void main() {
  setUpAll(() => HttpOverrides.global = null);

  testWidgets('scanned item lines are editable and the totals are computed from them', (tester) async {
    await _pumpScreen(tester);

    expect(find.text('Items on this bill'), findsOneWidget);
    expect(find.text('3 items'), findsOneWidget);
    expect(find.text('Gauze swab'), findsOneWidget);
    expect(find.text('Scissor'), findsOneWidget);
    expect(find.text('AED 55.54'), findsWidgets); // sum of items == printed total
    // No single-amount fields in multi mode -- the money comes from the lines.
    expect(find.textContaining('Amount excl. VAT (AED) *'), findsNothing);
    expect(find.text('Expense type *'), findsNothing);
  });

  testWidgets('submit sends the lines, line-derived totals and the main category', (tester) async {
    final api = await _pumpScreen(tester);

    // Correct the scissor price and give it its own category.
    await tester.enterText(find.widgetWithText(TextField, '7.66'), '10.00');
    await tester.pumpAndSettle();
    expect(find.text('AED 57.88'), findsWidgets);
    // Bill printed 55.54, items now 57.88: the mismatch is called out.
    expect(find.textContaining('differs by AED 2.34'), findsOneWidget);

    await tester.tap(find.text('Submit for approval'));
    await tester.pumpAndSettle();

    final body = api.createdBody!;
    expect(body['line_items'], [
      {'description': 'Gauze swab', 'quantity': 5.0, 'amount': 23.94, 'category_id': 1},
      {'description': 'Cotton wool', 'quantity': 5.0, 'amount': 23.94, 'category_id': 1},
      {'description': 'Scissor', 'quantity': 1.0, 'amount': 10.0, 'category_id': 1},
    ]);
    expect(body['total_amount'], 57.88);
    expect(body['amount'], 57.88);
    expect(body['category_id'], 1);
    expect(find.text('claim 99'), findsOneWidget);
  });

  testWidgets('an incomplete line blocks submit and says what is missing', (tester) async {
    final api = await _pumpScreen(tester);

    await tester.tap(find.text('Add item'));
    await tester.pumpAndSettle();
    expect(find.text('4 items'), findsOneWidget);

    await tester.tap(find.text('Submit for approval'));
    await tester.pumpAndSettle();

    expect(api.createdBody, isNull);
    expect(find.textContaining('Item 4: Add the item name'), findsOneWidget);
  });

  testWidgets('removing a line updates the total', (tester) async {
    await _pumpScreen(tester);
    await tester.tap(find.byTooltip('Remove item').last);
    await tester.pumpAndSettle();
    expect(find.text('2 items'), findsOneWidget);
    expect(find.text('Scissor'), findsNothing);
    expect(find.text('AED 47.88'), findsWidgets);
    expect(_field('Item *'), findsNWidgets(2));
  });
}

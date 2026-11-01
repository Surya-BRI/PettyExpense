import 'dart:io';

import 'package:expense_app/src/widgets/receipt_pages_view.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

// 1x1 transparent PNG.
const _png = <int>[
  0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
  0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
  0x89, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
  0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,
  0x42, 0x60, 0x82,
];

void main() {
  late Directory dir;
  late List<String> paths;

  setUpAll(() {
    dir = Directory.systemTemp.createTempSync('receipt_pages_test');
    paths = [
      for (var i = 1; i <= 3; i++) (File('${dir.path}/p$i.png')..writeAsBytesSync(_png)).path,
    ];
  });

  tearDownAll(() => dir.deleteSync(recursive: true));

  Future<void> pump(WidgetTester tester, List<String> pages) => tester.pumpWidget(
        MaterialApp(
          home: Scaffold(body: ReceiptPagesView.local(pages, height: 200)),
        ),
      );

  testWidgets('a one-page bill shows just the image, no counter', (tester) async {
    await pump(tester, paths.take(1).toList());

    expect(find.byType(Image), findsOneWidget);
    expect(find.byType(PageView), findsNothing);
    expect(find.textContaining('/ '), findsNothing);
    expect(find.text('Prev'), findsNothing);
    expect(find.text('Next'), findsNothing);
  });

  testWidgets('a multi-page bill swipes between pages with a counter', (tester) async {
    await pump(tester, paths);

    expect(find.text('1 / 3'), findsOneWidget);

    await tester.drag(find.byType(PageView), const Offset(-600, 0));
    await tester.pumpAndSettle();

    expect(find.text('2 / 3'), findsOneWidget);
  });

  testWidgets('Prev and Next under the image step through pages', (tester) async {
    await pump(tester, paths);

    final prev = tester.widget<TextButton>(
      find.ancestor(of: find.text('Prev'), matching: find.byType(TextButton)),
    );
    expect(prev.onPressed, isNull);
    expect(find.text('1 / 3'), findsOneWidget);

    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    expect(find.text('2 / 3'), findsOneWidget);

    await tester.tap(find.text('Next'));
    await tester.pumpAndSettle();
    expect(find.text('3 / 3'), findsOneWidget);
    final next = tester.widget<TextButton>(
      find.ancestor(of: find.text('Next'), matching: find.byType(TextButton)),
    );
    expect(next.onPressed, isNull);

    await tester.tap(find.text('Prev'));
    await tester.pumpAndSettle();
    expect(find.text('2 / 3'), findsOneWidget);
  });
}

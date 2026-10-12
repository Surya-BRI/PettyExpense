import 'package:expense_app/src/features/claims/capture_receipt_sheet.dart';
import 'package:expense_app/src/theme/app_theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

Future<void> _openSheet(WidgetTester tester) async {
  await tester.pumpWidget(
    ProviderScope(
      child: MaterialApp(
        theme: ThemeData(useMaterial3: true),
        home: Consumer(
          builder: (context, ref, _) => Scaffold(
            backgroundColor: AppColors.background,
            body: Center(
              child: TextButton(
                onPressed: () => showCaptureReceiptSheet(context, ref),
                child: const Text('open'),
              ),
            ),
          ),
        ),
      ),
    ),
  );
  await tester.tap(find.text('open'));
  await tester.pumpAndSettle();
}

ButtonStyleButton _button(WidgetTester tester, String label) =>
    tester.widget<ButtonStyleButton>(find.ancestor(of: find.text(label), matching: find.bySubtype<ButtonStyleButton>()).first);

void main() {
  testWidgets('camera and gallery stay disabled until a bill type is chosen', (tester) async {
    await _openSheet(tester);

    expect(find.text('Single item'), findsOneWidget);
    expect(find.text('Multiple items'), findsOneWidget);
    expect(find.text('Choose the bill type above to continue'), findsOneWidget);
    expect(_button(tester, 'Open camera').onPressed, isNull);
    expect(_button(tester, 'Upload from gallery').onPressed, isNull);

    await tester.tap(find.text('Multiple items'));
    await tester.pumpAndSettle();

    expect(find.text('Choose the bill type above to continue'), findsNothing);
    expect(_button(tester, 'Open camera').onPressed, isNotNull);
    expect(_button(tester, 'Upload from gallery').onPressed, isNotNull);
  });

  testWidgets('only one bill type can be selected at a time', (tester) async {
    await _openSheet(tester);

    await tester.tap(find.text('Single item'));
    await tester.pumpAndSettle();
    expect(find.byIcon(Icons.check_circle), findsOneWidget);
    expect(find.byIcon(Icons.circle_outlined), findsOneWidget);

    await tester.tap(find.text('Multiple items'));
    await tester.pumpAndSettle();
    // Still exactly one selected -- the choice moved, it did not add a second.
    expect(find.byIcon(Icons.check_circle), findsOneWidget);
    expect(find.byIcon(Icons.circle_outlined), findsOneWidget);
  });
}

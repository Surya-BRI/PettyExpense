import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:expense_app/main.dart';

void main() {
  testWidgets('App boots to home', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: ExpenseApp()));
    await tester.pumpAndSettle();
    expect(find.textContaining('Expense'), findsWidgets);
  });
}

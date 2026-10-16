import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:expense_app/main.dart';

void main() {
  testWidgets('App boots to home', (WidgetTester tester) async {
    // main() loads .env before runApp; the config reads it as soon as the app builds.
    dotenv.loadFromString(envString: 'API_BASE_URL=http://fake');
    await tester.pumpWidget(const ProviderScope(child: ExpenseApp()));
    await tester.pumpAndSettle();
    expect(find.text('My claims'), findsWidgets);
  });
}

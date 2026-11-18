import 'package:expense_app/src/features/approvals/backup_approver_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  late List<Map<String, dynamic>> backups;
  late List<List<Object>> saved;
  late List<int> removed;

  Map<String, dynamic> person(int id, String name, String role) =>
      {'id': id, 'display_name': name, 'role_label': role, 'department_name': null};

  Future<Map<String, dynamic>> load() async => {
        'today': '2026-11-17',
        'backups': backups,
        'candidates': [person(2, 'Priya', 'Head of Department'), person(3, 'Omar', 'Finance Manager')],
      };

  Widget panel() => MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: BackupApproverPanel(
              whose: 'your',
              load: load,
              save: (id, start, end) async {
                saved.add([id, start, end]);
                backups = [
                  {
                    'id': 9,
                    'backup': person(id, id == 3 ? 'Omar' : 'Priya', id == 3 ? 'Finance Manager' : 'Head of Department'),
                    'start_date': start,
                    'end_date': end,
                    'is_active': true,
                  },
                ];
              },
              remove: (id) async {
                removed.add(id);
                backups = [];
              },
            ),
          ),
        ),
      );

  setUp(() {
    backups = [];
    saved = [];
    removed = [];
  });

  testWidgets('approver sets a backup for today and tomorrow, then removes it', (tester) async {
    await tester.pumpWidget(panel());
    await tester.pumpAndSettle();
    expect(find.text('No backup set.'), findsOneWidget);

    await tester.tap(find.text('Set backup'));
    await tester.pumpAndSettle();

    // Save without a person is refused.
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();
    expect(find.text('Choose the backup approver'), findsOneWidget);
    expect(saved, isEmpty);

    await tester.tap(find.byKey(const Key('backup_person')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Omar · Finance Manager').last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    // Dates default to today -> tomorrow (Gulf date from the server).
    expect(saved, [
      [3, '2026-11-17', '2026-11-18'],
    ]);
    expect(find.text('Omar · Finance Manager'), findsOneWidget);
    expect(find.text('17 Nov 2026 – 18 Nov 2026'), findsOneWidget);
    expect(find.text('Active now'), findsOneWidget);

    await tester.tap(find.text('Remove').first);
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Remove'));
    await tester.pumpAndSettle();
    expect(removed, [9]);
    expect(find.text('No backup set.'), findsOneWidget);
  });
}

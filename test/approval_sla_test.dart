import 'package:expense_app/src/api/api_client.dart';
import 'package:expense_app/src/api/models.dart';
import 'package:expense_app/src/features/admin/aging_report_screen.dart';
import 'package:expense_app/src/features/admin/approval_time_limits_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeApi extends ApiClient {
  _FakeApi() : super(baseUrl: 'http://fake');

  Map<String, double>? saved;

  Map<String, dynamic> _sla(double hodHours) => {
        'region_id': 1,
        'min_hours': 5 / 60,
        'max_hours': 720,
        'stages': [
          {'stage': 'hod', 'label': 'Head of Department (HOD)', 'hours': hodHours},
          {'stage': 'finance_manager', 'label': 'Finance Manager', 'hours': 48},
        ],
      };

  @override
  Future<Map<String, dynamic>> regionSla(int regionId) async => _sla(saved?['hod'] ?? 24);

  @override
  Future<Map<String, dynamic>> updateRegionSla(int regionId, Map<String, double> hoursByStage) async {
    saved = hoursByStage;
    return _sla(hoursByStage['hod']!);
  }

  @override
  Future<List<RegionConfig>> listRegions() async => const [];
}

Widget _wrap(_FakeApi api, Widget child) => ProviderScope(
      overrides: [apiClientProvider.overrideWithValue(api)],
      child: MaterialApp(home: Scaffold(body: SingleChildScrollView(child: child))),
    );

void main() {
  test('formatSlaHours', () {
    expect(formatSlaHours(0.25), '15 min');
    expect(formatSlaHours(1), '1 hr');
    expect(formatSlaHours(24), '24 hrs');
    expect(formatSlaHours(28.5), '28 hrs 30 min');
    expect(formatSlaHours(48), '48 hrs');
  });

  testWidgets('SLA time button opens the sheet; Admin sets HOD to 15 minutes', (tester) async {
    final api = _FakeApi();
    await tester.pumpWidget(_wrap(api, const SlaTimeButton(regionId: 1)));
    await tester.pumpAndSettle();

    // Only the button on the tab -- no fields until it is tapped.
    expect(find.byKey(const Key('sla_hod_hours')), findsNothing);
    await tester.tap(find.text('SLA time'));
    await tester.pumpAndSettle();

    // Sheet opens straight on the fields, showing the current values.
    final hodHours = tester.widget<TextField>(find.byKey(const Key('sla_hod_hours')));
    expect(hodHours.controller!.text, '24');
    await tester.enterText(find.byKey(const Key('sla_hod_hours')), '0');
    await tester.enterText(find.byKey(const Key('sla_hod_minutes')), '15');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(api.saved, {'hod': 0.25, 'finance_manager': 48.0});
    expect(find.byKey(const Key('sla_hod_hours')), findsNothing); // sheet closed
    expect(find.text('SLA time saved'), findsOneWidget);
  });

  testWidgets('a time limit under 5 minutes is not saved', (tester) async {
    final api = _FakeApi();
    await tester.pumpWidget(_wrap(api, const SlaTimeButton(regionId: 1)));
    await tester.pumpAndSettle();
    await tester.tap(find.text('SLA time'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('sla_hod_hours')), '0');
    await tester.enterText(find.byKey(const Key('sla_hod_minutes')), '2');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();

    expect(api.saved, isNull);
    expect(find.textContaining('between 5 minutes and 720 hours'), findsOneWidget);
  });

  testWidgets('Aging report shows breached and escalated bills', (tester) async {
    final api = _FakeApi();
    final data = {
      'summary': {
        'pending': 2,
        'on_time': 0,
        'breached': 1,
        'escalated': 1,
        'buckets': {'under_1_day': 1, '1_3_days': 1},
      },
      'bucket_labels': {'under_1_day': 'Under 24 hrs', '1_3_days': '24–72 hrs'},
      'items': [
        {
          'transaction_id': 1234,
          'employee_name': 'Ahmed',
          'company': 'BRI UAE · Blue Rhine Industries',
          'vendor': 'ENOC',
          'total_amount': 150,
          'currency': 'AED',
          'stage_label': 'Sales HOD',
          'approvers': ['Rashid'],
          'stage_due_at': '2026-11-16T06:00:00',
          'waiting_text': '51 hrs',
          'overdue_text': '27 hrs',
          'sla_status': 'escalated',
        },
        {
          'transaction_id': 1240,
          'employee_name': 'Sara',
          'total_amount': 80,
          'currency': 'AED',
          'stage_label': 'Accountant',
          'approvers': ['Accounts'],
          'stage_due_at': '2026-11-17T06:00:00',
          'waiting_text': '20 hrs',
          'overdue_text': '2 hrs',
          'sla_status': 'breached',
        },
      ],
    };
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiClientProvider.overrideWithValue(api)],
        child: MaterialApp(home: Scaffold(body: AgingReportView(data: data))),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Escalated'), findsWidgets); // summary tile + badge
    expect(find.text('SLA breached'), findsOneWidget);
    expect(find.text('#1234 · Ahmed'), findsOneWidget);
    expect(find.text('With Sales HOD: Rashid'), findsOneWidget);
    expect(find.text('Waiting 51 hrs'), findsOneWidget);
    expect(find.textContaining('Overdue by 27 hrs'), findsOneWidget);
    expect(find.text('Under 24 hrs: 1'), findsOneWidget);
  });
}

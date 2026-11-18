import 'package:expense_app/src/features/claims/bill_line_mode.dart';
import 'package:expense_app/src/features/claims/offline_bills_card.dart';
import 'package:expense_app/src/services/offline_bills/offline_bill_store.dart';
import 'package:expense_app/src/services/offline_bills/offline_bill_sync.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

/// Shows a fixed list; records removes.
class _FakeBills extends StateNotifier<List<OfflineBill>> implements OfflineBillsController {
  _FakeBills(super.state);

  final removed = <String>[];

  @override
  Future<void> remove(String id) async {
    removed.add(id);
    state = [for (final b in state) if (b.id != id) b];
  }

  @override
  Future<int> sync() async => 0;

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

OfflineBill _bill(String id, String status, {int pages = 1}) => OfflineBill(
      id: id,
      userId: 1,
      pagePaths: [for (var i = 0; i < pages; i++) '/nowhere/$id-$i.jpg'],
      lineMode: BillLineMode.multiple,
      ocrMode: 'ar',
      createdAt: DateTime(2026, 11, 17),
      status: status,
      receiptId: status == OfflineBill.ready ? 55 : null,
      s3Key: status == OfflineBill.ready ? 'k55' : null,
    );

void main() {
  testWidgets('shows waiting and ready bills; a ready bill opens the confirm screen', (tester) async {
    final fake = _FakeBills([
      _bill('w1', OfflineBill.waiting),
      _bill('r1', OfflineBill.ready, pages: 2),
    ]);
    Object? confirmExtra;
    final router = GoRouter(
      initialLocation: '/claims',
      routes: [
        GoRoute(path: '/claims', builder: (_, _) => const Scaffold(body: OfflineBillsCard())),
        GoRoute(
          path: '/confirm',
          builder: (_, state) {
            confirmExtra = state.extra;
            return const Scaffold(body: Text('confirm screen'));
          },
        ),
      ],
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: [offlineBillsProvider.overrideWith((ref) => fake)],
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Ready to review (1)'), findsOneWidget);
    expect(find.text('Waiting to upload (1)'), findsOneWidget);
    expect(find.text('2 pages'), findsOneWidget);
    expect(find.text('Retry now'), findsOneWidget);

    await tester.tap(find.byKey(const Key('offline_bill_r1')));
    await tester.pumpAndSettle();
    expect(find.text('confirm screen'), findsOneWidget);
    final extra = confirmExtra as Map;
    expect(extra['offlineBillId'], 'r1');
    expect(extra['runOcr'], isTrue);
    expect(extra['lineMode'], BillLineMode.multiple);
    expect(extra['ocrMode'], 'ar');
    expect(extra['localPaths'], hasLength(2));
  });

  testWidgets('discarding a waiting bill asks first, then removes it', (tester) async {
    final fake = _FakeBills([_bill('w1', OfflineBill.waiting)]);
    await tester.pumpWidget(
      ProviderScope(
        overrides: [offlineBillsProvider.overrideWith((ref) => fake)],
        child: const MaterialApp(home: Scaffold(body: OfflineBillsCard())),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('discard_offline_bill_w1')));
    await tester.pumpAndSettle();
    expect(find.text('Discard this bill?'), findsOneWidget);
    await tester.tap(find.text('Discard'));
    await tester.pumpAndSettle();

    expect(fake.removed, ['w1']);
    expect(find.text('Waiting to upload (1)'), findsNothing);
  });

  testWidgets('nothing is shown when there are no offline bills', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [offlineBillsProvider.overrideWith((ref) => _FakeBills(const []))],
        child: const MaterialApp(home: Scaffold(body: OfflineBillsCard())),
      ),
    );
    expect(find.textContaining('upload'), findsNothing);
  });
}

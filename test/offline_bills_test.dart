import 'dart:io';

import 'package:expense_app/src/api/api_client.dart';
import 'package:expense_app/src/api/models.dart';
import 'package:expense_app/src/features/authentication/auth_controller.dart';
import 'package:expense_app/src/features/claims/bill_line_mode.dart';
import 'package:expense_app/src/services/offline_bills/offline_bill_store.dart';
import 'package:expense_app/src/services/offline_bills/offline_bill_sync.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// Upload behaviour is switched per test: offline, server error or success.
class _FakeApi extends ApiClient {
  _FakeApi() : super(baseUrl: 'http://fake');

  Object? failWith;
  int uploads = 0;

  @override
  Future<OcrResult> uploadReceipt(List<File> pages) async {
    if (failWith != null) throw failWith!;
    uploads++;
    return OcrResult(receiptId: 100 + uploads, s3Key: 'key$uploads', vendor: '', date: '');
  }
}

void main() {
  late Directory tmp;
  late Directory root;
  late _FakeApi api;

  setUp(() async {
    tmp = await Directory.systemTemp.createTemp('offline_bills_test');
    root = Directory('${tmp.path}/store');
    api = _FakeApi();
  });

  tearDown(() async {
    if (await tmp.exists()) await tmp.delete(recursive: true);
  });

  ProviderContainer container({int userId = 7}) {
    final c = ProviderContainer(
      overrides: [
        offlineBillRootProvider.overrideWith((ref) async => root),
        apiClientProvider.overrideWithValue(api),
        authControllerProvider.overrideWith(
          (ref) => AuthController.withState(
            AuthState(user: AuthUser(id: userId, displayName: 'Emp', role: 'employee', regionCode: 'KSA')),
          ),
        ),
      ],
    );
    addTearDown(c.dispose);
    return c;
  }

  Future<String> scan(String name) async {
    final f = File('${tmp.path}/$name.jpg');
    await f.writeAsBytes([1, 2, 3]);
    return f.path;
  }

  test('a bill scanned offline is kept on the phone, with its pages copied', () async {
    final c = container();
    final page1 = await scan('p1');
    final page2 = await scan('p2');
    final bill = await c.read(offlineBillsProvider.notifier).add([page1, page2], BillLineMode.multiple, 'ar');

    expect(bill, isNotNull);
    expect(bill!.status, OfflineBill.waiting);
    expect(bill.pagePaths, hasLength(2));
    expect(bill.pagePaths.every((p) => p.startsWith(root.path)), isTrue);
    // The scanner's own file can be wiped -- our copy stays.
    await File(page1).delete();
    expect(File(bill.pagePaths.first).existsSync(), isTrue);

    // Still there after the app restarts.
    final again = container();
    await again.read(offlineBillsProvider.notifier).sync(); // loads; api fails nothing here
    final reloaded = await OfflineBillStore(root).loadAll();
    expect(reloaded.single.lineMode, BillLineMode.multiple);
    expect(reloaded.single.ocrMode, 'ar');
  });

  test('when back online the bill uploads and is ready to review', () async {
    final c = container();
    api.failWith = const SocketException('offline');
    await c.read(offlineBillsProvider.notifier).add([await scan('p')], BillLineMode.single, 'auto');

    // Still offline: nothing uploaded, bill stays waiting.
    expect(await c.read(offlineBillsProvider.notifier).sync(), 0);
    expect(c.read(offlineBillsProvider).single.status, OfflineBill.waiting);
    expect(c.read(offlineBillsProvider).single.lastError, isNull);

    api.failWith = null;
    expect(await c.read(offlineBillsProvider.notifier).sync(), 1);
    final bill = c.read(offlineBillsProvider).single;
    expect(bill.status, OfflineBill.ready);
    expect(bill.receiptId, 101);
    expect(bill.s3Key, 'key1');

    // Already uploaded: a later sync doesn't send it again.
    expect(await c.read(offlineBillsProvider.notifier).sync(), 0);
    expect(api.uploads, 1);
  });

  test('a server refusal is shown on the bill and it can be retried', () async {
    final c = container();
    await c.read(offlineBillsProvider.notifier).add([await scan('p')], BillLineMode.single, 'auto');
    api.failWith = ApiException(413, 'File too large');

    expect(await c.read(offlineBillsProvider.notifier).sync(), 0);
    final bill = c.read(offlineBillsProvider).single;
    expect(bill.status, OfflineBill.waiting);
    expect(bill.lastError, 'File too large');
  });

  test('saving or discarding removes the bill and its photos', () async {
    final c = container();
    final bill = await c.read(offlineBillsProvider.notifier).add([await scan('p')], BillLineMode.single, 'auto');
    await c.read(offlineBillsProvider.notifier).remove(bill!.id);
    expect(c.read(offlineBillsProvider), isEmpty);
    expect(File(bill.pagePaths.first).existsSync(), isFalse);
  });

  test('an upload cut off by the app closing is tried again', () async {
    final c = container();
    final bill = await c.read(offlineBillsProvider.notifier).add([await scan('p')], BillLineMode.single, 'auto');
    final store = OfflineBillStore(root);
    await store.saveAll([bill!.copyWith(status: OfflineBill.uploading)]);
    expect((await store.loadAll()).single.status, OfflineBill.waiting);
  });

  test("each person only sees and uploads their own bills", () async {
    final a = container(userId: 7);
    await a.read(offlineBillsProvider.notifier).add([await scan('p')], BillLineMode.single, 'auto');

    final b = container(userId: 8);
    expect(await b.read(offlineBillsProvider.notifier).sync(), 0);
    expect(b.read(offlineBillsProvider), isEmpty);
    expect(api.uploads, 0);
  });

  test('only real "no connection" errors count as offline', () {
    expect(isOfflineError(const SocketException('x')), isTrue);
    expect(isOfflineError(ApiException(500, 'x')), isFalse);
    expect(isOfflineError(Exception('x')), isFalse);
  });
}

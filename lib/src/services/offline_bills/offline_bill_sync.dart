import 'dart:async';
import 'dart:io';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:path_provider/path_provider.dart';

import '../../api/api_client.dart';
import '../../features/authentication/auth_controller.dart';
import '../../features/claims/bill_line_mode.dart';
import 'offline_bill_store.dart';

/// Where offline bills are kept on the phone (tests override it with a temp folder).
final offlineBillRootProvider = FutureProvider<Directory>((ref) async {
  final docs = await getApplicationDocumentsDirectory();
  return Directory('${docs.path}${Platform.pathSeparator}offline_bills');
});

/// The signed-in user's offline bills (waiting to upload, or uploaded and ready to review).
final offlineBillsProvider = StateNotifierProvider<OfflineBillsController, List<OfflineBill>>((ref) {
  final userId = ref.watch(authControllerProvider.select((s) => s.user?.id));
  return OfflineBillsController(ref, userId);
});

class OfflineBillsController extends StateNotifier<List<OfflineBill>> {
  OfflineBillsController(this._ref, this._userId) : super(const []) {
    if (_userId != null) unawaited(_load());
  }

  final Ref _ref;
  final int? _userId;
  OfflineBillStore? _store;
  List<OfflineBill> _all = [];
  Future<void>? _loading;
  bool _syncing = false;

  Future<OfflineBillStore> _ensureStore() async {
    return _store ??= OfflineBillStore(await _ref.read(offlineBillRootProvider.future));
  }

  Future<void> _load() => _loading ??= () async {
        final store = await _ensureStore();
        _all = await store.loadAll();
        _publish();
      }();

  void _publish() {
    if (!mounted) return;
    state = [
      for (final b in _all)
        if (b.userId == _userId) b,
    ];
  }

  Future<void> _save() async {
    await (await _ensureStore()).saveAll(_all);
    _publish();
  }

  void _replace(OfflineBill bill) {
    _all = [for (final b in _all) b.id == bill.id ? bill : b];
  }

  /// Keeps a bill the phone couldn't upload. Returns it, or null when nobody is signed in.
  Future<OfflineBill?> add(List<String> pagePaths, BillLineMode lineMode, String ocrMode) async {
    final userId = _userId;
    if (userId == null) return null;
    await _load();
    final bill = await (await _ensureStore()).createBill(
      userId: userId,
      pagePaths: pagePaths,
      lineMode: lineMode,
      ocrMode: ocrMode,
    );
    _all = [..._all, bill];
    await _save();
    return bill;
  }

  /// Submitted / saved as a draft, or discarded: forget the bill and delete its pages.
  Future<void> remove(String id) async {
    await _load();
    final bill = _all.where((b) => b.id == id).firstOrNull;
    if (bill == null) return;
    _all = [for (final b in _all) if (b.id != id) b];
    await _save();
    await (await _ensureStore()).deleteFiles(bill);
  }

  /// Uploads the user's waiting bills, one by one. Stops at the first "still offline" and
  /// returns how many were uploaded this time. Safe to call often -- one run at a time.
  Future<int> sync() async {
    if (_userId == null || _syncing) return 0;
    _syncing = true;
    var uploaded = 0;
    try {
      await _load();
      final api = _ref.read(apiClientProvider);
      final waiting = [for (final b in _all) if (b.userId == _userId && b.status == OfflineBill.waiting) b];
      for (final bill in waiting) {
        if (!mounted) break;
        _replace(bill.copyWith(status: OfflineBill.uploading));
        await _save();
        try {
          final missing = [for (final p in bill.pagePaths) if (!File(p).existsSync()) p];
          if (missing.isNotEmpty) throw const FileSystemException('The saved bill photo is missing');
          final result = await api.uploadReceipt([for (final p in bill.pagePaths) File(p)]);
          _replace(bill.copyWith(
            status: OfflineBill.ready,
            receiptId: result.receiptId,
            s3Key: result.s3Key,
            clearError: true,
          ));
          uploaded++;
          await _save();
        } catch (e) {
          if (isOfflineError(e)) {
            _replace(bill.copyWith(status: OfflineBill.waiting));
            await _save();
            break; // still no connection: try again on the next trigger
          }
          _replace(bill.copyWith(status: OfflineBill.waiting, lastError: _message(e)));
          await _save();
        }
      }
    } finally {
      _syncing = false;
    }
    return uploaded;
  }

  static String _message(Object e) {
    if (e is FileSystemException) return e.message;
    final text = e.toString();
    return text.startsWith('Exception: ') ? text.substring(11) : text;
  }
}

/// Runs the offline-bill upload when the app starts, when the connection comes back and when
/// the app returns to the foreground; tells the user once bills are uploaded.
class OfflineBillSyncListener extends ConsumerStatefulWidget {
  const OfflineBillSyncListener({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<OfflineBillSyncListener> createState() => _OfflineBillSyncListenerState();
}

class _OfflineBillSyncListenerState extends ConsumerState<OfflineBillSyncListener> {
  StreamSubscription<List<ConnectivityResult>>? _connectivity;
  AppLifecycleListener? _lifecycle;

  @override
  void initState() {
    super.initState();
    if (kIsWeb) return; // capture (and so the offline queue) is mobile-only
    WidgetsBinding.instance.addPostFrameCallback((_) => _sync());
    _lifecycle = AppLifecycleListener(onResume: _sync);
    try {
      _connectivity = Connectivity().onConnectivityChanged.listen(
        (results) {
          if (results.any((r) => r != ConnectivityResult.none)) _sync();
        },
        onError: (_) {}, // no connectivity plugin (tests): app start / resume still sync
      );
    } catch (_) {}
  }

  @override
  void dispose() {
    _connectivity?.cancel();
    _lifecycle?.dispose();
    super.dispose();
  }

  Future<void> _sync() async {
    if (!mounted) return;
    final n = await ref.read(offlineBillsProvider.notifier).sync();
    if (!mounted || n == 0) return;
    ScaffoldMessenger.maybeOf(context)?.showSnackBar(
      SnackBar(
        content: Text(n == 1
            ? '1 bill uploaded. Open it in Claims to check and submit.'
            : '$n bills uploaded. Open them in Claims to check and submit.'),
        action: SnackBarAction(label: 'Review', onPressed: () => context.go('/claims')),
      ),
    );
  }

  @override
  Widget build(BuildContext context) => widget.child;
}

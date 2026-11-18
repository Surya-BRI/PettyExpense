import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../../features/claims/bill_line_mode.dart';

/// A bill scanned while the phone was offline (Spec Section 2, Offline handling).
///
/// waiting   -- pages saved on the phone, not uploaded yet
/// uploading -- upload in progress
/// ready     -- uploaded; the employee opens it, the app reads it and they check and submit
class OfflineBill {
  const OfflineBill({
    required this.id,
    required this.userId,
    required this.pagePaths,
    required this.lineMode,
    required this.ocrMode,
    required this.createdAt,
    this.status = OfflineBill.waiting,
    this.receiptId,
    this.s3Key,
    this.lastError,
  });

  static const waiting = 'waiting';
  static const uploading = 'uploading';
  static const ready = 'ready';

  final String id;
  final int userId;
  final List<String> pagePaths;
  final BillLineMode lineMode;
  final String ocrMode;
  final DateTime createdAt;
  final String status;
  final int? receiptId;
  final String? s3Key;

  /// Last upload failure that wasn't "no connection" (e.g. the server refused the file).
  final String? lastError;

  bool get isReady => status == ready;

  OfflineBill copyWith({String? status, int? receiptId, String? s3Key, String? lastError, bool clearError = false}) =>
      OfflineBill(
        id: id,
        userId: userId,
        pagePaths: pagePaths,
        lineMode: lineMode,
        ocrMode: ocrMode,
        createdAt: createdAt,
        status: status ?? this.status,
        receiptId: receiptId ?? this.receiptId,
        s3Key: s3Key ?? this.s3Key,
        lastError: clearError ? null : (lastError ?? this.lastError),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'user_id': userId,
        'pages': pagePaths,
        'line_mode': lineMode.name,
        'ocr_mode': ocrMode,
        'created_at': createdAt.toIso8601String(),
        'status': status,
        'receipt_id': receiptId,
        's3_key': s3Key,
        'last_error': lastError,
      };

  factory OfflineBill.fromJson(Map<String, dynamic> j) => OfflineBill(
        id: j['id'] as String,
        userId: (j['user_id'] as num).toInt(),
        pagePaths: [for (final p in (j['pages'] as List? ?? const [])) '$p'],
        lineMode: BillLineMode.values.firstWhere(
          (m) => m.name == j['line_mode'],
          orElse: () => BillLineMode.single,
        ),
        ocrMode: j['ocr_mode'] as String? ?? 'auto',
        createdAt: DateTime.tryParse(j['created_at'] as String? ?? '') ?? DateTime.now(),
        status: j['status'] as String? ?? waiting,
        receiptId: (j['receipt_id'] as num?)?.toInt(),
        s3Key: j['s3_key'] as String?,
        lastError: j['last_error'] as String?,
      );
}

/// True when [e] means the phone couldn't reach the server (no data / Wi-Fi, DNS, timeout) --
/// as opposed to the server answering with an error, which isn't fixed by waiting.
bool isOfflineError(Object e) =>
    e is SocketException || e is http.ClientException || e is TimeoutException || e is HandshakeException;

/// Keeps offline bills on the phone: pages under `<root>/<userId>/<billId>/` and the list in
/// `<root>/queue.json`. Pages are copied in, because the scanner's own files live in a cache
/// folder the phone may clear.
class OfflineBillStore {
  OfflineBillStore(this.root);

  final Directory root;

  File get _queueFile => File('${root.path}${Platform.pathSeparator}queue.json');

  Future<List<OfflineBill>> loadAll() async {
    try {
      if (!await _queueFile.exists()) return [];
      final raw = jsonDecode(await _queueFile.readAsString());
      return [
        for (final j in (raw as List))
          // An upload cut off by the app closing never finished: try it again.
          () {
            final b = OfflineBill.fromJson(Map<String, dynamic>.from(j as Map));
            return b.status == OfflineBill.uploading ? b.copyWith(status: OfflineBill.waiting) : b;
          }(),
      ];
    } catch (_) {
      return []; // unreadable file: start clean rather than crash the claims screen
    }
  }

  Future<void> saveAll(List<OfflineBill> bills) async {
    await root.create(recursive: true);
    final tmp = File('${_queueFile.path}.tmp');
    await tmp.writeAsString(jsonEncode([for (final b in bills) b.toJson()]));
    await tmp.rename(_queueFile.path); // never leave a half-written list behind
  }

  /// Copies the pages into the store and returns the new bill (not yet saved to the list).
  Future<OfflineBill> createBill({
    required int userId,
    required List<String> pagePaths,
    required BillLineMode lineMode,
    required String ocrMode,
  }) async {
    final id = DateTime.now().microsecondsSinceEpoch.toString();
    final dir = Directory('${root.path}${Platform.pathSeparator}$userId${Platform.pathSeparator}$id');
    await dir.create(recursive: true);
    final copied = <String>[];
    for (var i = 0; i < pagePaths.length; i++) {
      final src = File(pagePaths[i]);
      final dot = src.path.lastIndexOf('.');
      final ext = dot > src.path.lastIndexOf(Platform.pathSeparator) ? src.path.substring(dot) : '.jpg';
      final dest = '${dir.path}${Platform.pathSeparator}page_${i + 1}$ext';
      await src.copy(dest);
      copied.add(dest);
    }
    return OfflineBill(
      id: id,
      userId: userId,
      pagePaths: copied,
      lineMode: lineMode,
      ocrMode: ocrMode,
      createdAt: DateTime.now(),
    );
  }

  Future<void> deleteFiles(OfflineBill bill) async {
    final dir = Directory('${root.path}${Platform.pathSeparator}${bill.userId}${Platform.pathSeparator}${bill.id}');
    try {
      if (await dir.exists()) await dir.delete(recursive: true);
    } catch (_) {
      // A leftover folder is harmless; never block removing the bill from the list.
    }
  }
}

import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;

import '../features/authentication/auth_controller.dart';
import 'api_config.dart';
import 'models.dart';

/// Prefer [resolveApiBase] — kept for older imports.
String get kDefaultApiBase => resolveApiBase();

final apiClientProvider = Provider<ApiClient>((ref) {
  final auth = ref.watch(authControllerProvider);
  return ApiClient(
    baseUrl: resolveApiBase(),
    accessToken: auth.accessToken,
    // Called on any 401 — refreshes the session and hands back a new token to
    // retry with. `ref.read` (not watch): this fires well after this provider
    // was built, not during it.
    onUnauthorized: () => ref.read(authControllerProvider.notifier).refreshOnUnauthorized(),
  );
});

class ApiClient {
  ApiClient({required this.baseUrl, String? accessToken, this.onUnauthorized})
      : _accessToken = accessToken;

  final String baseUrl;
  final Future<String?> Function()? onUnauthorized;
  String? _accessToken;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_accessToken != null && _accessToken!.isNotEmpty)
          'Authorization': 'Bearer $_accessToken',
      };

  Uri _uri(String path, [Map<String, String>? query]) {
    final uri = Uri.parse('$baseUrl$path').replace(queryParameters: query);
    if (kDebugMode) debugPrint('[API] → $uri');
    return uri;
  }

  /// Runs an authenticated request; on a 401, refreshes the access token once
  /// via [onUnauthorized] and retries exactly once with the new token before
  /// giving up. `request` is re-invoked (not just re-headered) so multipart
  /// bodies get rebuilt fresh — `http.MultipartRequest` can't be resent as-is.
  Future<http.Response> _authorized(
    Future<http.Response> Function() request,
  ) async {
    var res = await request();
    if (res.statusCode == 401 && onUnauthorized != null) {
      final newToken = await onUnauthorized!();
      if (newToken != null && newToken.isNotEmpty) {
        _accessToken = newToken;
        res = await request();
      }
    }
    return res;
  }

  Future<Map<String, dynamic>> login(String username, String password) async {
    final res = await http.post(
      _uri('/api/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );
    return _decodeMap(res);
  }

  Future<AuthUser> me() async {
    final res = await _authorized(() => http.get(_uri('/api/auth/me'), headers: _headers));
    return AuthUser.fromJson(_decodeMap(res));
  }

  Future<Map<String, dynamic>> refresh(String refreshToken) async {
    final res = await http.post(
      _uri('/api/auth/refresh'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'refresh_token': refreshToken}),
    );
    return _decodeMap(res);
  }

  Future<OcrResult> uploadReceipt(File file) async {
    final res = await _authorized(() async {
      final req = http.MultipartRequest('POST', _uri('/api/claims/ocr/upload'));
      if (_accessToken != null && _accessToken!.isNotEmpty) {
        req.headers['Authorization'] = 'Bearer $_accessToken';
      }
      req.files.add(await http.MultipartFile.fromPath('file', file.path));
      final streamed = await req.send();
      return http.Response.fromStream(streamed);
    });
    return OcrResult.fromJson(_decodeMap(res));
  }

  Future<OcrResult> analyzeReceipt(int receiptId) async {
    final res = await _authorized(() {
      final headers = <String, String>{
        if (_accessToken != null && _accessToken!.isNotEmpty) 'Authorization': 'Bearer $_accessToken',
      };
      return http
          .post(_uri('/api/claims/receipts/$receiptId/ocr'), headers: headers)
          .timeout(const Duration(seconds: 120));
    });
    return OcrResult.fromJson(_decodeMap(res));
  }

  Future<OcrResult> uploadOcr(File file) async {
    return uploadReceipt(file);
  }

  Future<ExpenseClaim> createClaim(Map<String, dynamic> body) async {
    final res = await _authorized(() => http.post(
          _uri('/api/claims'),
          headers: _headers,
          body: jsonEncode(body),
        ));
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<ExpenseClaim> updateDraft(int id, Map<String, dynamic> body) async {
    final res = await _authorized(() => http.patch(
          _uri('/api/claims/$id'),
          headers: _headers,
          body: jsonEncode(body),
        ));
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<ExpenseClaim> submitClaim(int id) async {
    final res = await _authorized(() => http.post(_uri('/api/claims/$id/submit'), headers: _headers));
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  /// After a dispute: employee corrects the bill and resubmits. Returns to the exact
  /// stage that disputed it (backend keeps current_stage untouched on resubmit).
  Future<ExpenseClaim> resubmitClaim(int id) async {
    final res = await _authorized(() => http.post(_uri('/api/claims/$id/resubmit'), headers: _headers));
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<List<ExpenseClaim>> myClaims() async {
    final res = await _authorized(() => http.get(_uri('/api/claims/mine'), headers: _headers));
    final list = _decodeList(res);
    return list.map((e) => ExpenseClaim.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ExpenseClaim> getClaim(int id) async {
    final res = await _authorized(() => http.get(_uri('/api/claims/$id'), headers: _headers));
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<List<CategoryRef>> categories() async {
    final res = await _authorized(() => http.get(_uri('/api/categories'), headers: _headers));
    final list = _decodeList(res);
    return list.map((e) => CategoryRef.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<ExpenseClaim>> adminClaims({
    String? status,
    int? categoryId,
    int? employeeId,
    int? projectId,
  }) async {
    final query = <String, String>{};
    if (status != null && status.isNotEmpty) query['status'] = status;
    if (categoryId != null) query['category_id'] = '$categoryId';
    if (employeeId != null) query['employee_id'] = '$employeeId';
    if (projectId != null) query['project_id'] = '$projectId';
    final res = await _authorized(
      () => http.get(_uri('/api/admin/claims', query.isEmpty ? null : query), headers: _headers),
    );
    final list = _decodeList(res);
    return list.map((e) => ExpenseClaim.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ExpenseClaim> markPaid(int id, {String? remarks}) async {
    final res = await _authorized(() => http.post(
          _uri('/api/admin/claims/$id/mark-paid'),
          headers: _headers,
          body: jsonEncode({'remarks': remarks}),
        ));
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  // -- Approvals (Phase 2 multi-stage workflow) --

  Future<List<ExpenseClaim>> approvalsQueue(String stage) async {
    final res = await _authorized(() => http.get(_uri('/api/approvals/queue', {'stage': stage}), headers: _headers));
    final list = _decodeList(res);
    return list.map((e) => ExpenseClaim.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ExpenseClaim> getApprovalTransaction(int id) async {
    final res = await _authorized(() => http.get(_uri('/api/approvals/$id'), headers: _headers));
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<ExpenseClaim> approveTransaction(int id, {String? comment}) async {
    final res = await _authorized(() => http.post(
          _uri('/api/approvals/$id/approve'),
          headers: _headers,
          body: jsonEncode({'comment': comment}),
        ));
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<ExpenseClaim> disputeTransaction(int id, {required String comment}) async {
    final res = await _authorized(() => http.post(
          _uri('/api/approvals/$id/dispute'),
          headers: _headers,
          body: jsonEncode({'comment': comment}),
        ));
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<ExpenseClaim> rejectTransaction(int id, {required String comment}) async {
    final res = await _authorized(() => http.post(
          _uri('/api/approvals/$id/reject'),
          headers: _headers,
          body: jsonEncode({'comment': comment}),
        ));
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<Map<String, dynamic>> bulkApprove(List<int> transactionIds) async {
    final res = await _authorized(() => http.post(
          _uri('/api/approvals/bulk-approve'),
          headers: _headers,
          body: jsonEncode({'transaction_ids': transactionIds}),
        ));
    return _decodeMap(res);
  }

  Future<List<ProjectRef>> projects() async {
    final res = await _authorized(() => http.get(_uri('/api/projects'), headers: _headers));
    final list = _decodeList(res);
    return list.map((e) => ProjectRef.fromJson(e as Map<String, dynamic>)).toList();
  }

  String imageUrl(String? path) {
    if (path == null || path.isEmpty) return '';
    if (path.startsWith('http')) return path;
    return '$baseUrl$path';
  }

  /// Fetches receipt image bytes. A presigned S3 URL (what `image_url` usually
  /// is when S3 storage is configured) is already fully authorized via its own
  /// signature — attaching our own bearer token on top makes S3 reject the
  /// request outright (400 "Only one auth mechanism allowed"), so those go out
  /// with no extra headers at all. Only our own backend proxy path needs (and
  /// gets) the 401-retry treatment every other call goes through.
  Future<Uint8List> fetchImageBytes(String path) async {
    final url = imageUrl(path);
    final res = url.startsWith('http')
        ? await http.get(Uri.parse(url))
        : await _authorized(() => http.get(Uri.parse(url), headers: _headers));
    if (res.statusCode >= 400) {
      throw ApiException(res.statusCode, 'Failed to load image');
    }
    return res.bodyBytes;
  }

  Map<String, dynamic> _decodeMap(http.Response res) {
    final body = res.body.isEmpty ? <String, dynamic>{} : jsonDecode(res.body);
    if (res.statusCode >= 400) {
      final detail = body is Map ? body['detail'] : body;
      throw ApiException(res.statusCode, detail?.toString() ?? 'Request failed');
    }
    return Map<String, dynamic>.from(body as Map);
  }

  List<dynamic> _decodeList(http.Response res) {
    final body = res.body.isEmpty ? [] : jsonDecode(res.body);
    if (res.statusCode >= 400) {
      final detail = body is Map ? body['detail'] : body;
      throw ApiException(res.statusCode, detail?.toString() ?? 'Request failed');
    }
    return body as List<dynamic>;
  }
}

class ApiException implements Exception {
  ApiException(this.statusCode, this.message);
  final int statusCode;
  final String message;

  @override
  String toString() => 'ApiException($statusCode): $message';
}

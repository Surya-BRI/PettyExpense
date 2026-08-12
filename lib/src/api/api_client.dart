import 'dart:convert';
import 'dart:io';

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
  );
});

class ApiClient {
  ApiClient({required this.baseUrl, this.accessToken});

  final String baseUrl;
  final String? accessToken;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (accessToken != null && accessToken!.isNotEmpty)
          'Authorization': 'Bearer $accessToken',
      };

  Uri _uri(String path, [Map<String, String>? query]) {
    return Uri.parse('$baseUrl$path').replace(queryParameters: query);
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
    final res = await http.get(_uri('/api/auth/me'), headers: _headers);
    return AuthUser.fromJson(_decodeMap(res));
  }

  Future<OcrResult> uploadOcr(File file) async {
    final req = http.MultipartRequest('POST', _uri('/api/claims/ocr'));
    if (accessToken != null && accessToken!.isNotEmpty) {
      req.headers['Authorization'] = 'Bearer $accessToken';
    }
    req.files.add(await http.MultipartFile.fromPath('file', file.path));
    final streamed = await req.send();
    final res = await http.Response.fromStream(streamed);
    return OcrResult.fromJson(_decodeMap(res));
  }

  Future<ExpenseClaim> createClaim(Map<String, dynamic> body) async {
    final res = await http.post(
      _uri('/api/claims'),
      headers: _headers,
      body: jsonEncode(body),
    );
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<ExpenseClaim> updateDraft(int id, Map<String, dynamic> body) async {
    final res = await http.patch(
      _uri('/api/claims/$id'),
      headers: _headers,
      body: jsonEncode(body),
    );
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<ExpenseClaim> submitClaim(int id) async {
    final res = await http.post(_uri('/api/claims/$id/submit'), headers: _headers);
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  /// After a dispute: employee corrects the bill and resubmits. Returns to the exact
  /// stage that disputed it (backend keeps current_stage untouched on resubmit).
  Future<ExpenseClaim> resubmitClaim(int id) async {
    final res = await http.post(_uri('/api/claims/$id/resubmit'), headers: _headers);
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<List<ExpenseClaim>> myClaims() async {
    final res = await http.get(_uri('/api/claims/mine'), headers: _headers);
    final list = _decodeList(res);
    return list.map((e) => ExpenseClaim.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ExpenseClaim> getClaim(int id) async {
    final res = await http.get(_uri('/api/claims/$id'), headers: _headers);
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<List<CategoryRef>> categories() async {
    final res = await http.get(_uri('/api/categories'), headers: _headers);
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
    final res = await http.get(_uri('/api/admin/claims', query.isEmpty ? null : query), headers: _headers);
    final list = _decodeList(res);
    return list.map((e) => ExpenseClaim.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ExpenseClaim> markPaid(int id, {String? remarks}) async {
    final res = await http.post(
      _uri('/api/admin/claims/$id/mark-paid'),
      headers: _headers,
      body: jsonEncode({'remarks': remarks}),
    );
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  // -- Approvals (Phase 2 multi-stage workflow) --

  Future<List<ExpenseClaim>> approvalsQueue(String stage) async {
    final res = await http.get(_uri('/api/approvals/queue', {'stage': stage}), headers: _headers);
    final list = _decodeList(res);
    return list.map((e) => ExpenseClaim.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ExpenseClaim> getApprovalTransaction(int id) async {
    final res = await http.get(_uri('/api/approvals/$id'), headers: _headers);
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<ExpenseClaim> approveTransaction(int id, {String? comment}) async {
    final res = await http.post(
      _uri('/api/approvals/$id/approve'),
      headers: _headers,
      body: jsonEncode({'comment': comment}),
    );
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<ExpenseClaim> disputeTransaction(int id, {required String comment}) async {
    final res = await http.post(
      _uri('/api/approvals/$id/dispute'),
      headers: _headers,
      body: jsonEncode({'comment': comment}),
    );
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<ExpenseClaim> rejectTransaction(int id, {required String comment}) async {
    final res = await http.post(
      _uri('/api/approvals/$id/reject'),
      headers: _headers,
      body: jsonEncode({'comment': comment}),
    );
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<Map<String, dynamic>> bulkApprove(List<int> transactionIds) async {
    final res = await http.post(
      _uri('/api/approvals/bulk-approve'),
      headers: _headers,
      body: jsonEncode({'transaction_ids': transactionIds}),
    );
    return _decodeMap(res);
  }

  Future<List<ProjectRef>> projects() async {
    final res = await http.get(_uri('/api/projects'), headers: _headers);
    final list = _decodeList(res);
    return list.map((e) => ProjectRef.fromJson(e as Map<String, dynamic>)).toList();
  }

  String imageUrl(String? path) {
    if (path == null || path.isEmpty) return '';
    if (path.startsWith('http')) return path;
    return '$baseUrl$path';
  }

  Map<String, String> authHeaders() => {
        if (accessToken != null && accessToken!.isNotEmpty)
          'Authorization': 'Bearer $accessToken',
      };

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

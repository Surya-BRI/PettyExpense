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
    // Called on any 401 to refresh the session; `ref.read` (not watch) since this fires well after the provider was built.
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

  /// On a 401, refreshes the token via [onUnauthorized] and retries once by re-invoking `request` (multipart bodies can't just be re-headered).
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

  Future<Map<String, dynamic>> login(String username, String password, {String? regionCode}) async {
    final res = await http.post(
      _uri('/api/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password, 'region_code': regionCode}),
    );
    if (res.statusCode == 400) {
      final body = res.body.isEmpty ? <String, dynamic>{} : jsonDecode(res.body);
      final detail = body is Map ? body['detail'] : null;
      if (detail is Map && detail['region_required'] == true) {
        throw RegionSelectionRequired(
          List<String>.from(detail['allowed_regions'] as List? ?? const []),
        );
      }
    }
    return _decodeMap(res);
  }

  /// Re-issues the session under another of the user's assigned companies.
  Future<Map<String, dynamic>> switchRegion(String regionCode) async {
    final res = await _authorized(() => http.post(
          _uri('/api/auth/switch-region'),
          headers: _headers,
          body: jsonEncode({'region_code': regionCode}),
        ));
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

  /// [pages] are the pages of one bill in order: the first goes as `file`,
  /// the rest as repeated `pages` fields.
  Future<OcrResult> uploadReceipt(List<File> pages) async {
    final res = await _authorized(() async {
      final req = http.MultipartRequest('POST', _uri('/api/claims/ocr/upload'));
      if (_accessToken != null && _accessToken!.isNotEmpty) {
        req.headers['Authorization'] = 'Bearer $_accessToken';
      }
      req.files.add(await http.MultipartFile.fromPath('file', pages.first.path));
      for (final page in pages.skip(1)) {
        req.files.add(await http.MultipartFile.fromPath('pages', page.path));
      }
      final streamed = await req.send();
      return http.Response.fromStream(streamed);
    });
    return OcrResult.fromJson(_decodeMap(res));
  }

  Future<OcrResult> analyzeReceipt(int receiptId, {String mode = 'auto'}) async {
    final res = await _authorized(() {
      final headers = <String, String>{
        if (_accessToken != null && _accessToken!.isNotEmpty) 'Authorization': 'Bearer $_accessToken',
      };
      return http
          .post(
            _uri('/api/claims/receipts/$receiptId/ocr', {'mode': mode}),
            headers: headers,
          )
          // Multi-page bills take longer (the server allows +20s per extra page).
          .timeout(const Duration(seconds: 180));
    });
    return OcrResult.fromJson(_decodeMap(res));
  }

  Future<OcrResult> uploadOcr(File file) async {
    return uploadReceipt([file]);
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

  /// After a dispute: employee corrects the bill and resubmits, returning to the exact stage that disputed it (backend keeps current_stage untouched).
  Future<ExpenseClaim> resubmitClaim(int id) async {
    final res = await _authorized(() => http.post(_uri('/api/claims/$id/resubmit'), headers: _headers));
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  Future<ClaimsPage> myClaims({int limit = 6, int offset = 0, String? status, String? regionCode}) async {
    final res = await _authorized(() => http.get(
          _uri('/api/claims/mine', {
            'limit': '$limit',
            'offset': '$offset',
            if (status != null && status != 'all') 'status': status,
            if (regionCode != null && regionCode.isNotEmpty) 'region_code': regionCode,
          }),
          headers: _headers,
        ));
    final map = _decodeMap(res);
    final items = (map['items'] as List)
        .map((e) => ExpenseClaim.fromJson(e as Map<String, dynamic>))
        .toList();
    return ClaimsPage(
      items: items,
      total: (map['total'] as num).toInt(),
      offset: (map['offset'] as num).toInt(),
      limit: (map['limit'] as num).toInt(),
    );
  }

  Future<ExpenseClaim> getClaim(int id) async {
    final res = await _authorized(() => http.get(_uri('/api/claims/$id'), headers: _headers));
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  /// Preview rate for 1 [from] in [to], or in [regionCode]'s base currency when [to] is null.
  Future<ExchangeRateQuote> lookupExchangeRate({
    required String from,
    String? to,
    String? regionCode,
    String? date,
  }) async {
    final query = <String, String>{
      'from': from,
      if (to != null && to.isNotEmpty) 'to': to,
      if (regionCode != null && regionCode.isNotEmpty) 'region_code': regionCode,
    };
    if (date != null && date.trim().isNotEmpty) query['date'] = date.trim();
    final res = await _authorized(
      () => http.get(_uri('/api/claims/exchange-rate', query), headers: _headers),
    );
    return ExchangeRateQuote.fromJson(_decodeMap(res));
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

  Future<List<ActivityItem>> activity({int limit = 50}) async {
    final res = await _authorized(
      () => http.get(_uri('/api/admin/activity', {'limit': '$limit'}), headers: _headers),
    );
    return _decodeList(res).map((e) => ActivityItem.fromJson(e as Map<String, dynamic>)).toList();
  }

  // -- Payments (approved reimbursements → paid) --

  Future<PaymentsPage> listPayments({
    String status = 'unpaid',
    String? regionCode,
    int limit = 50,
    int offset = 0,
  }) async {
    final query = <String, String>{
      'status': status,
      'limit': '$limit',
      'offset': '$offset',
      if (regionCode != null && regionCode.isNotEmpty) 'region_code': regionCode,
    };
    final res = await _authorized(() => http.get(_uri('/api/payments', query), headers: _headers));
    return PaymentsPage.fromJson(_decodeMap(res));
  }

  /// [method] for Dubai-style payments; [source] instead at Professional Signs: 'bank'
  /// (Process 1, cash withdrawal from bank) or 'accounts_petty_cash' (Process 2, direct payment).
  Future<PaymentRecord> recordPayment({
    required int claimId,
    String? method,
    String? source,
    required String reference,
    required String paymentDate,
    String? remarks,
  }) async {
    final res = await _authorized(() => http.post(
          _uri('/api/payments'),
          headers: _headers,
          body: jsonEncode({
            'transaction_id': claimId,
            'payment_method': ?method,
            'payment_source': ?source,
            'payment_reference': reference,
            'payment_date': paymentDate,
            'remarks': remarks,
          }),
        ));
    return PaymentRecord.fromJson(_decodeMap(res));
  }

  /// One payment (same process/method, reference and date) for several approved bills.
  Future<({int paid, List<String> skipped})> recordPaymentBatch({
    required List<int> claimIds,
    String? method,
    String? source,
    required String reference,
    required String paymentDate,
    String? remarks,
  }) async {
    final res = await _authorized(() => http.post(
          _uri('/api/payments/batch'),
          headers: _headers,
          body: jsonEncode({
            'transaction_ids': claimIds,
            'payment_method': ?method,
            'payment_source': ?source,
            'payment_reference': reference,
            'payment_date': paymentDate,
            'remarks': remarks,
          }),
        ));
    final body = _decodeMap(res);
    return (
      paid: (body['paid'] as List? ?? const []).length,
      skipped: [
        for (final s in (body['skipped'] as List? ?? const []))
          if (s is Map) '#${s['id']}: ${s['reason']}',
      ],
    );
  }

  // -- Approvals (Phase 2 multi-stage workflow) --

  Future<List<Map<String, dynamic>>> approvalsHistory({int limit = 100}) async {
    final res = await _authorized(() => http.get(_uri('/api/approvals/history', {'limit': '$limit'}), headers: _headers));
    return _decodeList(res).cast<Map<String, dynamic>>();
  }

  Future<List<ExpenseClaim>> approvalsQueue(String stage) async {
    final res = await _authorized(() => http.get(_uri('/api/approvals/queue', {'stage': stage}), headers: _headers));
    final list = _decodeList(res);
    return list.map((e) => ExpenseClaim.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ExpenseClaim> getApprovalTransaction(int id) async {
    final res = await _authorized(() => http.get(_uri('/api/approvals/$id'), headers: _headers));
    return ExpenseClaim.fromJson(_decodeMap(res));
  }

  /// [journalType] (EJV | EJVB) and [journalReference] are required at a company's journal
  /// stage (Professional Signs: Accounts).
  Future<ExpenseClaim> approveTransaction(
    int id, {
    String? comment,
    String? journalType,
    String? journalReference,
  }) async {
    final res = await _authorized(() => http.post(
          _uri('/api/approvals/$id/approve'),
          headers: _headers,
          body: jsonEncode({
            'comment': comment,
            'journal_type': ?journalType,
            'journal_reference': ?journalReference,
          }),
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

  Future<OpportunityResult?> searchOpportunity(String code) async {
    final res = await _authorized(
      () => http.get(_uri('/api/opportunities/search', {'code': code.trim()}), headers: _headers),
    );
    if (res.statusCode == 200 && res.body != 'null' && res.body.isNotEmpty) {
      final map = _decodeMap(res);
      return OpportunityResult.fromJson(map);
    }
    return null;
  }

  // -- Notifications (email handled server-side; this is just the in-app feed) --

  Future<List<Map<String, dynamic>>> notifications({int limit = 20, int offset = 0}) async {
    final res = await _authorized(() => http.get(
          _uri('/api/notifications', {'limit': '$limit', 'offset': '$offset'}),
          headers: _headers,
        ));
    return _decodeList(res).cast<Map<String, dynamic>>();
  }

  Future<int> unreadNotificationCount() async {
    final res = await _authorized(() => http.get(_uri('/api/notifications/unread-count'), headers: _headers));
    return (_decodeMap(res)['unread'] as num).toInt();
  }

  Future<void> markNotificationRead(int id) async {
    await _authorized(() => http.post(_uri('/api/notifications/$id/read'), headers: _headers));
  }

  Future<void> markAllNotificationsRead() async {
    await _authorized(() => http.post(_uri('/api/notifications/read-all'), headers: _headers));
  }

  Future<List<RegionConfig>> listRegions() async {
    var res = await _authorized(() => http.get(_uri('/api/regions'), headers: _headers));
    if (res.statusCode == 404) {
      res = await _authorized(() => http.get(_uri('/api/admin/config/regions'), headers: _headers));
    }
    return [
      for (final row in _decodeList(res))
        if (Map<String, dynamic>.from(row as Map)['region_code']?.toString().toUpperCase() != 'IN')
          RegionConfig.fromJson(Map<String, dynamic>.from(row as Map)),
    ];
  }

  Future<RegionConfig> getBranding(String regionCode) async {
    final res = await _authorized(() => http.get(_uri('/api/branding/$regionCode'), headers: _headers));
    return RegionConfig.fromJson(_decodeMap(res));
  }

  Future<RegionConfig> updateRegion(int regionId, {String? companyName}) async {
    final res = await _authorized(() => http.put(
          _uri('/api/admin/config/regions/$regionId'),
          headers: _headers,
          body: jsonEncode({if (companyName != null) 'company_name': companyName}),
        ));
    return RegionConfig.fromJson(_decodeMap(res));
  }

  Future<RegionConfig> uploadRegionLogo(int regionId, File file) async {
    final res = await _authorized(() async {
      final req = http.MultipartRequest('POST', _uri('/api/admin/config/regions/$regionId/logo'));
      if (_accessToken != null && _accessToken!.isNotEmpty) {
        req.headers['Authorization'] = 'Bearer $_accessToken';
      }
      req.files.add(await http.MultipartFile.fromPath('file', file.path));
      return http.Response.fromStream(await req.send());
    });
    return RegionConfig.fromJson(_decodeMap(res));
  }

  /// HODs, Accountants and Finance Managers who handle this company's bills (home company
  /// or assigned by Admin), plus `missing` roles that fall back to Admin.
  Future<Map<String, dynamic>> regionApprovers(int regionId) async {
    final res = await _authorized(
      () => http.get(_uri('/api/admin/config/regions/$regionId/approvers'), headers: _headers),
    );
    return _decodeMap(res);
  }

  Future<List<Map<String, dynamic>>> adminDepartments() async {
    final res = await _authorized(() => http.get(_uri('/api/admin/config/departments'), headers: _headers));
    return [for (final row in _decodeList(res)) Map<String, dynamic>.from(row as Map)];
  }

  Future<OrgUserPage> adminUsers({
    String? regionCode,
    String? q,
    int limit = 25,
    int offset = 0,
  }) async {
    final res = await _authorized(
      () => http.get(
        _uri('/api/admin/users', {
          if (regionCode != null && regionCode.isNotEmpty) 'region_code': regionCode,
          if (q != null && q.trim().isNotEmpty) 'q': q.trim(),
          'limit': '$limit',
          'offset': '$offset',
        }),
        headers: _headers,
      ),
    );
    return OrgUserPage.fromJson(_decodeMap(res));
  }

  Future<OrgUser> adminUser(int userId) async {
    final res = await _authorized(
      () => http.get(_uri('/api/admin/users/$userId'), headers: _headers),
    );
    return OrgUser.fromJson(_decodeMap(res));
  }

  Future<OrgUser> setUserRegions(int userId, List<String> regionCodes) async {
    final res = await _authorized(() => http.put(
          _uri('/api/admin/users/$userId/regions'),
          headers: _headers,
          body: jsonEncode({'region_codes': regionCodes}),
        ));
    return OrgUser.fromJson(_decodeMap(res));
  }

  Future<List<PettyCashFund>> adminFunds() async {
    final res = await _authorized(() => http.get(_uri('/api/admin/funds'), headers: _headers));
    return [for (final row in _decodeList(res)) PettyCashFund.fromJson(Map<String, dynamic>.from(row as Map))];
  }

  Future<List<DepartmentFund>> adminDepartmentFunds(int regionId) async {
    final res = await _authorized(() => http.get(
          _uri('/api/admin/department-funds', {'region_id': '$regionId'}),
          headers: _headers,
        ));
    return [for (final row in _decodeList(res)) DepartmentFund.fromJson(Map<String, dynamic>.from(row as Map))];
  }

  Future<PettyCashFund> createFund(Map<String, dynamic> body) async {
    final res = await _authorized(() => http.post(
          _uri('/api/admin/funds'),
          headers: _headers,
          body: jsonEncode(body),
        ));
    return PettyCashFund.fromJson(_decodeMap(res));
  }

  Future<PettyCashFund> updateFundOpening(int fundId, {required double openingBalance}) async {
    final res = await _authorized(() => http.put(
          _uri('/api/admin/funds/$fundId'),
          headers: _headers,
          body: jsonEncode({'opening_balance': openingBalance}),
        ));
    return PettyCashFund.fromJson(_decodeMap(res));
  }

  Future<PettyCashFund> creditFund(int fundId, {required double amount, String? remarks}) async {
    final res = await _authorized(() => http.post(
          _uri('/api/admin/funds/$fundId/credit'),
          headers: _headers,
          body: jsonEncode({'amount': amount, 'remarks': remarks}),
        ));
    return PettyCashFund.fromJson(_decodeMap(res));
  }

  Future<List<PettyCashFund>> myFunds() async {
    final res = await _authorized(() => http.get(_uri('/api/funds/mine'), headers: _headers));
    return [for (final row in _decodeList(res)) PettyCashFund.fromJson(Map<String, dynamic>.from(row as Map))];
  }

  Future<List<TopupRequest>> listTopups({String? status}) async {
    final res = await _authorized(() => http.get(
          _uri('/api/topups', {if (status != null) 'status': status}),
          headers: _headers,
        ));
    return [for (final row in _decodeList(res)) TopupRequest.fromJson(Map<String, dynamic>.from(row as Map))];
  }

  Future<List<ReplenishableBill>> replenishableBills(int fundId) async {
    final res = await _authorized(() => http.get(_uri('/api/funds/$fundId/replenishable-bills'), headers: _headers));
    return [for (final row in _decodeList(res)) ReplenishableBill.fromJson(Map<String, dynamic>.from(row as Map))];
  }

  Future<TopupRequest> createTopup(
    int fundId, {
    double? amount,
    String? remarks,
    List<int>? transactionIds,
  }) async {
    final res = await _authorized(() => http.post(
          _uri('/api/funds/$fundId/topups'),
          headers: _headers,
          body: jsonEncode({
            'amount': amount,
            'remarks': remarks,
            'transaction_ids': transactionIds,
          }),
        ));
    return TopupRequest.fromJson(_decodeMap(res));
  }

  Future<TopupRequest> verifyTopup(int id, {String? remarks}) async {
    final res = await _authorized(() => http.post(
          _uri('/api/topups/$id/verify'),
          headers: _headers,
          body: jsonEncode({'remarks': remarks}),
        ));
    return TopupRequest.fromJson(_decodeMap(res));
  }

  /// Accounts sends a top-up back to the HOD; [remarks] (the reason) is required.
  Future<TopupRequest> returnTopup(int id, {required String remarks}) async {
    final res = await _authorized(() => http.post(
          _uri('/api/topups/$id/return'),
          headers: _headers,
          body: jsonEncode({'remarks': remarks}),
        ));
    return TopupRequest.fromJson(_decodeMap(res));
  }

  Future<TopupRequest> decideTopup(
    int id, {
    required bool approve,
    String? remarks,
    String? paymentReference,
  }) async {
    final path = approve ? '/api/topups/$id/approve' : '/api/topups/$id/reject';
    final res = await _authorized(() => http.post(
          _uri(path),
          headers: _headers,
          body: jsonEncode({
            'remarks': remarks,
            if (approve) 'payment_method': 'bank_transfer',
            if (paymentReference != null) 'payment_reference': paymentReference,
          }),
        ));
    return TopupRequest.fromJson(_decodeMap(res));
  }

  // -- Employee petty cash advances (Professional Signs): /api/pca --

  List<TopupRequest> _requests(http.Response res) =>
      [for (final row in _decodeList(res)) TopupRequest.fromJson(Map<String, dynamic>.from(row as Map))];

  /// Advances with balances: an employee's own, an HOD's staff's, everyone's for Accounts,
  /// the Accounts Manager and Admin.
  Future<List<PettyCashFund>> pcaAdvances({int? regionId}) async {
    final res = await _authorized(() => http.get(
          _uri('/api/pca/advances', {if (regionId != null) 'region_id': '$regionId'}),
          headers: _headers,
        ));
    return [for (final row in _decodeList(res)) PettyCashFund.fromJson(Map<String, dynamic>.from(row as Map))];
  }

  Future<PcaSummary> pcaSummary(int regionId) async {
    final res = await _authorized(
      () => http.get(_uri('/api/pca/summary', {'region_id': '$regionId'}), headers: _headers),
    );
    return PcaSummary.fromJson(_decodeMap(res));
  }

  /// Employees tab: departments with counts only (fast).
  Future<PcaDepartments> pcaDepartments(int regionId) async {
    final res = await _authorized(
      () => http.get(_uri('/api/pca/departments', {'region_id': '$regionId'}), headers: _headers),
    );
    return PcaDepartments.fromJson(_decodeMap(res));
  }

  /// One department's employees with their petty cash figures (0 = no department).
  Future<PcaDepartmentEmployees> pcaDepartmentEmployees(int regionId, int departmentId) async {
    final res = await _authorized(
      () => http.get(
        _uri('/api/pca/departments/$departmentId/employees', {'region_id': '$regionId'}),
        headers: _headers,
      ),
    );
    return PcaDepartmentEmployees.fromJson(_decodeMap(res));
  }

  Future<List<PcaStaff>> pcaStaff(int regionId) async {
    final res = await _authorized(
      () => http.get(_uri('/api/pca/staff', {'region_id': '$regionId'}), headers: _headers),
    );
    return [for (final row in _decodeList(res)) PcaStaff.fromJson(Map<String, dynamic>.from(row as Map))];
  }

  Future<List<TopupRequest>> pcaRequests({String? status, String? kind}) async {
    final res = await _authorized(() => http.get(
          _uri('/api/pca/requests', {'status': ?status, 'kind': ?kind}),
          headers: _headers,
        ));
    return _requests(res);
  }

  Future<TopupRequest> proposeAdvance({
    required int regionId,
    required int employeeId,
    required double amount,
    String? remarks,
  }) async {
    final res = await _authorized(() => http.post(
          _uri('/api/pca/advances'),
          headers: _headers,
          body: jsonEncode({
            'region_id': regionId,
            'employee_id': employeeId,
            'amount': amount,
            'remarks': remarks,
          }),
        ));
    return TopupRequest.fromJson(_decodeMap(res));
  }

  Future<List<ReplenishableBill>> pcaReplenishableBills(int fundId) async {
    final res = await _authorized(
      () => http.get(_uri('/api/pca/advances/$fundId/replenishable-bills'), headers: _headers),
    );
    return [for (final row in _decodeList(res)) ReplenishableBill.fromJson(Map<String, dynamic>.from(row as Map))];
  }

  Future<TopupRequest> pcaRequestTopup(int fundId, {required List<int> transactionIds, String? remarks}) async {
    final res = await _authorized(() => http.post(
          _uri('/api/pca/advances/$fundId/topups'),
          headers: _headers,
          body: jsonEncode({'transaction_ids': transactionIds, 'remarks': remarks}),
        ));
    return TopupRequest.fromJson(_decodeMap(res));
  }

  /// One step of an advance / top-up: `hod-approve`, `manager-approve` or `reject`.
  Future<TopupRequest> pcaStep(int requestId, String step, {String? remarks}) async {
    final res = await _authorized(() => http.post(
          _uri('/api/pca/requests/$requestId/$step'),
          headers: _headers,
          body: jsonEncode({'remarks': remarks}),
        ));
    return TopupRequest.fromJson(_decodeMap(res));
  }

  Future<TopupRequest> pcaPay(
    int requestId, {
    required String source,
    required String method,
    required String reference,
    required String paymentDate,
    String? remarks,
  }) async {
    final res = await _authorized(() => http.post(
          _uri('/api/pca/requests/$requestId/pay'),
          headers: _headers,
          body: jsonEncode({
            'payment_source': source,
            'payment_method': method,
            'payment_reference': reference,
            'payment_date': paymentDate,
            'remarks': remarks,
          }),
        ));
    return TopupRequest.fromJson(_decodeMap(res));
  }

  // -- Site petty cash (Blue Rhine Contracting): /api/site-pca --

  /// Employee petty cash with balances: an employee's own; everyone's for Accounts, the Head
  /// of Accountant, the Finance Manager and Admin.
  Future<List<PettyCashFund>> sitePots({int? regionId, int? employeeId}) async {
    final res = await _authorized(() => http.get(
          _uri('/api/site-pca/pots', {
            if (regionId != null) 'region_id': '$regionId',
            if (employeeId != null) 'employee_id': '$employeeId',
          }),
          headers: _headers,
        ));
    return [for (final row in _decodeList(res)) PettyCashFund.fromJson(Map<String, dynamic>.from(row as Map))];
  }

  /// Everyone in the company, for the Accountant's "Set petty cash" picker.
  Future<List<PcaStaff>> sitePeople(int regionId) async {
    final res = await _authorized(
      () => http.get(_uri('/api/site-pca/people', {'region_id': '$regionId'}), headers: _headers),
    );
    return [for (final row in _decodeList(res)) PcaStaff.fromJson(Map<String, dynamic>.from(row as Map))];
  }

  /// Accountant / Admin: an employee's petty cash from now on (not an increase).
  Future<TopupRequest> setSitePot({
    required int regionId,
    required int employeeId,
    required double amount,
    String? remarks,
  }) async {
    final res = await _authorized(() => http.post(
          _uri('/api/site-pca/pots'),
          headers: _headers,
          body: jsonEncode({
            'region_id': regionId,
            'employee_id': employeeId,
            'amount': amount,
            'remarks': remarks,
          }),
        ));
    return TopupRequest.fromJson(_decodeMap(res));
  }

  Future<List<ReplenishableBill>> siteReplenishableBills(int fundId) async {
    final res = await _authorized(
      () => http.get(_uri('/api/site-pca/pots/$fundId/replenishable-bills'), headers: _headers),
    );
    return [for (final row in _decodeList(res)) ReplenishableBill.fromJson(Map<String, dynamic>.from(row as Map))];
  }

  /// Accountant / Admin: prepare a top-up from the pot's approved bills.
  Future<TopupRequest> siteRequestTopup(int fundId, {required List<int> transactionIds, String? remarks}) async {
    final res = await _authorized(() => http.post(
          _uri('/api/site-pca/pots/$fundId/topups'),
          headers: _headers,
          body: jsonEncode({'transaction_ids': transactionIds, 'remarks': remarks}),
        ));
    return TopupRequest.fromJson(_decodeMap(res));
  }

  Future<List<TopupRequest>> siteRequests({int? regionId, String? status, String? kind}) async {
    final res = await _authorized(() => http.get(
          _uri('/api/site-pca/requests', {
            if (regionId != null) 'region_id': '$regionId',
            'status': ?status,
            'kind': ?kind,
          }),
          headers: _headers,
        ));
    return _requests(res);
  }

  /// Head of Accountant / Admin: approve a top-up.
  Future<TopupRequest> siteApprove(int requestId, {String? remarks}) async {
    final res = await _authorized(() => http.post(
          _uri('/api/site-pca/requests/$requestId/approve'),
          headers: _headers,
          body: jsonEncode({'remarks': remarks}),
        ));
    return TopupRequest.fromJson(_decodeMap(res));
  }

  /// Finance Manager / Admin: approve and record the cash withdrawal from the bank.
  Future<TopupRequest> sitePay(
    int requestId, {
    required String method,
    required String reference,
    required String paymentDate,
    String? remarks,
  }) async {
    final res = await _authorized(() => http.post(
          _uri('/api/site-pca/requests/$requestId/pay'),
          headers: _headers,
          body: jsonEncode({
            'payment_method': method,
            'payment_reference': reference,
            'payment_date': paymentDate,
            'remarks': remarks,
          }),
        ));
    return TopupRequest.fromJson(_decodeMap(res));
  }

  Future<TopupRequest> siteReject(int requestId, {required String comment}) async {
    final res = await _authorized(() => http.post(
          _uri('/api/site-pca/requests/$requestId/reject'),
          headers: _headers,
          body: jsonEncode({'comment': comment}),
        ));
    return TopupRequest.fromJson(_decodeMap(res));
  }

  /// Admin: a person's app role (e.g. head_accountant, finance_manager).
  Future<void> setUserRole(int userId, String role) async {
    await _authorized(() => http.put(
          _uri('/api/admin/users/$userId/role'),
          headers: _headers,
          body: jsonEncode({'role': role}),
        ));
  }

  // -- Accounts Department petty cash (Professional Signs, PCA PDF section 6) --

  Future<AccountsCash> accountsCash(int regionId) async {
    final res = await _authorized(
      () => http.get(_uri('/api/pca/accounts-cash', {'region_id': '$regionId'}), headers: _headers),
    );
    return AccountsCash.fromJson(_decodeMap(res));
  }

  /// Admin only: the account's amount from now on.
  Future<AccountsCash> setAccountsCash(int regionId, double amount, {String? remarks}) async {
    final res = await _authorized(() => http.put(
          _uri('/api/pca/accounts-cash'),
          headers: _headers,
          body: jsonEncode({'region_id': regionId, 'amount': amount, 'remarks': remarks}),
        ));
    return AccountsCash.fromJson(_decodeMap(res));
  }

  /// Accounts Manager / Admin: money put back from the bank ([amount] null = all paid out).
  Future<AccountsCash> refillAccountsCash(
    int regionId, {
    double? amount,
    required String reference,
    required String refillDate,
    String? remarks,
  }) async {
    final res = await _authorized(() => http.post(
          _uri('/api/pca/accounts-cash/refills'),
          headers: _headers,
          body: jsonEncode({
            'region_id': regionId,
            'amount': amount,
            'reference': reference,
            'refill_date': refillDate,
            'remarks': remarks,
          }),
        ));
    return AccountsCash.fromJson(_decodeMap(res));
  }

  String imageUrl(String? path) {
    if (path == null || path.isEmpty) return '';
    if (path.startsWith('http')) return path;
    return '$baseUrl$path';
  }

  /// Fetches image bytes. Presigned S3 URLs are already self-authorized (a bearer
  /// header would make S3 reject them). Our own `/api/...` paths, including region
  /// logos, go through the 401-retry flow.
  Future<Uint8List> fetchImageBytes(String path) async {
    final url = imageUrl(path);
    final ours = path.startsWith('/') || url.startsWith(baseUrl);
    final res = ours
        ? await _authorized(() => http.get(Uri.parse(url), headers: _headers))
        : await http.get(Uri.parse(url));
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

class ClaimsPage {
  ClaimsPage({required this.items, required this.total, required this.offset, required this.limit});

  final List<ExpenseClaim> items;
  final int total;
  final int offset;
  final int limit;

  bool get hasMore => offset + items.length < total;
}

/// Thrown by [ApiClient.login] when the account is multi-region (see
/// `ErpExpenseMultiRegionUserRegion`) and must pick one of [allowedRegions] before the
/// login can complete. Single-region accounts never hit this -- their region is derived
/// server-side from ERP data.
class RegionSelectionRequired implements Exception {
  RegionSelectionRequired(this.allowedRegions);
  final List<String> allowedRegions;
}

class ApiException implements Exception {
  ApiException(this.statusCode, this.message);
  final int statusCode;
  final String message;

  /// What users see: the server's own message, never the status code or class name.
  @override
  String toString() {
    if (statusCode >= 500) return 'Something went wrong on the server. Please try again.';
    final text = message.trim();
    // Validation details come back as a list/map ("[{loc: ...}]"): not readable for users.
    if (text.isEmpty || text.startsWith('[') || text.startsWith('{')) {
      return 'Something isn\'t right with this request. Please check and try again.';
    }
    return text;
  }
}

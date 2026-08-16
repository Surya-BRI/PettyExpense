import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';

class AuthState {
  const AuthState({
    this.user,
    this.accessToken,
    this.refreshToken,
    this.isLoading = false,
    this.useMockBypass = true,
  });

  final AuthUser? user;
  final String? accessToken;
  final String? refreshToken;
  final bool isLoading;
  final bool useMockBypass;

  bool get isAuthenticated => user != null;

  AuthState copyWith({
    AuthUser? user,
    String? accessToken,
    String? refreshToken,
    bool? isLoading,
    bool? useMockBypass,
    bool clearUser = false,
  }) {
    return AuthState(
      user: clearUser ? null : (user ?? this.user),
      accessToken: accessToken ?? this.accessToken,
      refreshToken: refreshToken ?? this.refreshToken,
      isLoading: isLoading ?? this.isLoading,
      useMockBypass: useMockBypass ?? this.useMockBypass,
    );
  }
}

class AuthController extends StateNotifier<AuthState> {
  AuthController() : super(const AuthState()) {
    _bootstrap();
  }

  final _storage = const FlutterSecureStorage();

  Future<void> _bootstrap() async {
    state = state.copyWith(isLoading: true);
    final token = await _storage.read(key: 'access_token');
    final refresh = await _storage.read(key: 'refresh_token');
    if (token != null && token.isNotEmpty) {
      try {
        final client = ApiClient(baseUrl: kDefaultApiBase, accessToken: token);
        final me = await client.me();
        state = AuthState(
          user: me,
          accessToken: token,
          refreshToken: refresh,
          useMockBypass: false,
        );
        return;
      } catch (_) {
        // Access tokens are short-lived (60 min) — this is the expected, common
        // case on every app reopen after that window, not just an edge case.
        // Try the 7-day refresh token before wiping the session and dropping
        // back to the mock user.
        if (await _tryRefresh(refresh) != null) return;
      }
    }
    await _fallbackToMock();
  }

  /// Shared by `_bootstrap` (app launch) and `refreshOnUnauthorized`
  /// (mid-session, called by `ApiClient` when a request comes back 401) — one
  /// place that knows how to turn a refresh token into a new session.
  /// Returns the new access token, or null if the refresh token itself is
  /// missing/expired/invalid.
  Future<String?> _tryRefresh(String? refreshToken) async {
    if (refreshToken == null || refreshToken.isEmpty) return null;
    try {
      final client = ApiClient(baseUrl: kDefaultApiBase);
      final data = await client.refresh(refreshToken);
      final user = AuthUser.fromJson(data['user'] as Map<String, dynamic>);
      final access = data['access_token'] as String;
      final newRefresh = data['refresh_token'] as String;
      await _storage.write(key: 'access_token', value: access);
      await _storage.write(key: 'refresh_token', value: newRefresh);
      state = AuthState(
        user: user,
        accessToken: access,
        refreshToken: newRefresh,
        useMockBypass: false,
      );
      return access;
    } catch (_) {
      return null;
    }
  }

  Future<void> _fallbackToMock() async {
    await _storage.deleteAll();
    // Phase-friendly mock bypass until an employee logs in
    state = const AuthState(
      user: AuthUser(
        id: 0,
        displayName: 'Mock Employee',
        role: 'employee',
        username: 'salesman',
      ),
      useMockBypass: true,
    );
  }

  /// Called by `ApiClient` when any authenticated request comes back 401 —
  /// tries the refresh token so the request can be retried once with a new
  /// access token, without the user noticing their session ever briefly
  /// invalidated. Falls back to the mock session if the refresh token itself
  /// is dead (matches `_bootstrap`'s behavior for that case).
  Future<String?> refreshOnUnauthorized() async {
    final refreshToken = state.refreshToken ?? await _storage.read(key: 'refresh_token');
    final access = await _tryRefresh(refreshToken);
    if (access == null) await _fallbackToMock();
    return access;
  }

  Future<void> login(String username, String password) async {
    state = state.copyWith(isLoading: true);
    final client = ApiClient(baseUrl: kDefaultApiBase);
    final data = await client.login(username, password);
    final user = AuthUser.fromJson(data['user'] as Map<String, dynamic>);
    final access = data['access_token'] as String;
    final refresh = data['refresh_token'] as String;
    await _storage.write(key: 'access_token', value: access);
    await _storage.write(key: 'refresh_token', value: refresh);
    state = AuthState(
      user: user,
      accessToken: access,
      refreshToken: refresh,
      useMockBypass: false,
    );
  }

  Future<void> logout() async {
    await _storage.deleteAll();
    // Clear session — go to login (do not force mock salesman)
    state = const AuthState(
      user: null,
      useMockBypass: false,
      isLoading: false,
    );
  }

  Future<void> continueAsMockSalesman() async {
    state = const AuthState(
      user: AuthUser(
        id: 0,
        displayName: 'Mock Employee',
        role: 'employee',
        username: 'salesman',
      ),
      useMockBypass: true,
    );
  }
}

final authControllerProvider =
    StateNotifierProvider<AuthController, AuthState>((ref) => AuthController());

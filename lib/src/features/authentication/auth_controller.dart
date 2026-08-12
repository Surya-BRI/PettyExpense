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
        await _storage.deleteAll();
      }
    }
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

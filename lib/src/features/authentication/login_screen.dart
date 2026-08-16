import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/enums.dart';
import '../../routing/role_routes.dart';
import '../../theme/app_theme.dart';
import 'auth_controller.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _DemoUser {
  const _DemoUser(this.username, this.password, this.label);
  final String username;
  final String password;
  final String label;
}

const _demoUsers = [
  _DemoUser('surya', 'surya123', 'Surya (Employee · Sales)'),
  _DemoUser('raghu', 'raghu123', 'Raghu (Employee · Sales)'),
  _DemoUser('vikram', 'vikram123', 'Vikram (Employee · IT)'),
  _DemoUser('denny', 'denny123', 'Denny (HOD · IT)'),
  _DemoUser('sajeesh', 'sajeesh123', 'Sajeesh (HOD · Sales)'),
  _DemoUser('anjana', 'anjana123', 'Anjana (Accountant)'),
  _DemoUser('sandeep', 'sandeep123', 'Sandeep (Finance Manager)'),
  _DemoUser('rajesh', 'rajesh123', 'Rajesh (Finance Manager)'),
  _DemoUser('teja', 'teja123', 'Teja (Admin)'),
];

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _userCtrl = TextEditingController(text: 'surya');
  final _passCtrl = TextEditingController(text: 'surya123');
  String? _selectedUsername = 'surya';
  String? _error;
  bool _busy = false;
  bool _obscurePassword = true;

  @override
  void dispose() {
    _userCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(authControllerProvider.notifier).login(
            _userCtrl.text.trim(),
            _passCtrl.text,
          );
      final user = ref.read(authControllerProvider).user;
      if (!mounted) return;
      context.go(homeRouteFor(UserRoleX.fromJson(user?.role)));
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _fill(String user, String pass) {
    setState(() {
      _selectedUsername = user;
      _userCtrl.text = user;
      _passCtrl.text = pass;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  minHeight: constraints.maxHeight - 32,
                  maxWidth: 420,
                ),
                child: IntrinsicHeight(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const Spacer(flex: 2),
                      // Full Blue Rhine logo — center of login (no title text)
                      Center(
                        child: Image.asset(
                          'assets/brand/Br_fulllogo.png',
                          width: MediaQuery.sizeOf(context).width * 0.72,
                          fit: BoxFit.contain,
                          errorBuilder: (_, __, ___) => Image.asset(
                            'assets/brand/logo_blue_rhine.png',
                            width: MediaQuery.sizeOf(context).width * 0.72,
                            fit: BoxFit.contain,
                          ),
                        ),
                      ),
                      const Spacer(flex: 2),
                      InputDecorator(
                        decoration: const InputDecoration(labelText: 'Demo user'),
                        child: DropdownButtonHideUnderline(
                          child: DropdownButton<String>(
                            isExpanded: true,
                            value: _selectedUsername,
                            items: _demoUsers
                                .map(
                                  (u) => DropdownMenuItem(
                                    value: u.username,
                                    child: Text(u.label),
                                  ),
                                )
                                .toList(),
                            onChanged: (username) {
                              final u = _demoUsers.firstWhere((d) => d.username == username);
                              _fill(u.username, u.password);
                            },
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),
                      TextField(
                        controller: _userCtrl,
                        decoration: const InputDecoration(labelText: 'Username'),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _passCtrl,
                        obscureText: _obscurePassword,
                        decoration: InputDecoration(
                          labelText: 'Password',
                          suffixIcon: IconButton(
                            icon: Icon(_obscurePassword ? Icons.visibility_off : Icons.visibility),
                            onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                          ),
                        ),
                      ),
                      if (_error != null) ...[
                        const SizedBox(height: 12),
                        Text(_error!, style: const TextStyle(color: AppColors.danger)),
                      ],
                      const SizedBox(height: 20),
                      FilledButton(
                        onPressed: _busy ? null : _login,
                        child: Text(_busy ? 'Signing in…' : 'Sign in'),
                      ),
                      const SizedBox(height: 12),
                      OutlinedButton(
                        onPressed: _busy
                            ? null
                            : () async {
                                await ref
                                    .read(authControllerProvider.notifier)
                                    .continueAsMockSalesman();
                                if (context.mounted) context.go('/claims');
                              },
                        child: const Text('Continue as mock salesman'),
                      ),
                      const Spacer(flex: 1),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

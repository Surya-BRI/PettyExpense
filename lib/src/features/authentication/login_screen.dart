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

const _regions = ['UAE', 'KSA', 'OMAN'];
const _regionLabels = {'UAE': 'UAE', 'KSA': 'KSA', 'OMAN': 'Oman'};

// Reference only -- type these into the fields above. Fatima is excluded here since her
// region choice is restricted (UAE/KSA/Oman only) rather than free like every account below.
const _demoAccounts = [
  ('surya', 'surya123', 'Employee · Sales'),
  ('raghu', 'raghu123', 'Employee · Sales'),
  ('vikram', 'vikram123', 'Employee · IT'),
  ('denny', 'denny123', 'HOD · IT'),
  ('sajeesh', 'sajeesh123', 'HOD · Sales'),
  ('anjana', 'anjana123', 'Accountant'),
  ('sandeep', 'sandeep123', 'Finance Manager'),
  ('rajesh', 'rajesh123', 'Finance Manager'),
  ('teja', 'teja123', 'Admin'),
];

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _userCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  String _selectedRegion = 'UAE';
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
            regionCode: _selectedRegion,
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
                      // Full Blue Rhine logo — center of login
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
                      const SizedBox(height: 12),
                      Text(
                        'Petty Cash and Expense Tracker',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const Spacer(flex: 2),
                      Text('Sign in as region', style: Theme.of(context).textTheme.labelMedium),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          for (final region in _regions) ...[
                            Expanded(child: _RegionPill(
                              label: _regionLabels[region] ?? region,
                              selected: _selectedRegion == region,
                              onTap: () => setState(() => _selectedRegion = region),
                            )),
                            if (region != _regions.last) const SizedBox(width: 10),
                          ],
                        ],
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
                      const SizedBox(height: 20),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: AppColors.divider),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Demo accounts — tap to fill in', style: Theme.of(context).textTheme.labelMedium),
                            const SizedBox(height: 4),
                            for (final (username, password, role) in _demoAccounts)
                              InkWell(
                                onTap: () => setState(() {
                                  _userCtrl.text = username;
                                  _passCtrl.text = password;
                                }),
                                child: Padding(
                                  padding: const EdgeInsets.symmetric(vertical: 4),
                                  child: Text(
                                    '$username / $password — $role',
                                    style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                                  ),
                                ),
                              ),
                          ],
                        ),
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

class _RegionPill extends StatelessWidget {
  const _RegionPill({required this.label, required this.selected, required this.onTap});

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: selected ? AppColors.darkBlue : AppColors.card,
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        borderRadius: BorderRadius.circular(10),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: selected ? AppColors.darkBlue : AppColors.divider),
          ),
          child: Text(
            label,
            style: TextStyle(
              fontWeight: FontWeight.w700,
              color: selected ? Colors.white : AppColors.textPrimary,
            ),
          ),
        ),
      ),
    );
  }
}

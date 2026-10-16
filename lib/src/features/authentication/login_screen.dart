import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';

import '../../api/api_client.dart' show RegionSelectionRequired;
import '../../api/enums.dart';
import '../../routing/role_routes.dart';
import '../../theme/app_theme.dart';
import 'auth_controller.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

const _regionLabels = {'UAE': 'UAE', 'KSA': 'KSA', 'OMAN': 'Oman'};

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _userCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  // Most accounts are single-region and never need this -- their region is derived
  // server-side from ERP data. These only get populated if /login comes back asking
  // the user to choose (RegionSelectionRequired), i.e. a genuine multi-region account.
  List<String>? _regionOptions;
  String? _selectedRegion;
  String? _error;
  bool _busy = false;
  bool _obscurePassword = true;

  static const _demoAccounts = [
    ('surya_sales_emp',    'Test@1234', 'Employee · Sales'),
    ('priya_sales_hod',    'Test@1234', 'HOD · Sales'),
    ('anjana_it_emp',      'Test@1234', 'Employee · IT'),
    ('vikram_it_hod',      'Test@1234', 'HOD · IT'),
    ('deepa_accounts_emp', 'Test@1234', 'Employee · Accounts'),
    ('ravi_accountant',    'Test@1234', 'Accountant'),
    ('meera_finance_mgr',  'Test@1234', 'Finance Manager'),
    ('arjun_admin',        'Test@1234', 'Admin'),
    ('dev_uae',            'Test@1234', 'Employee · UAE region'),
    ('dev_ksa',            'Test@1234', 'Employee · KSA region'),
    ('dev_oman',           'Test@1234', 'Employee · OMAN region'),
  ];

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
    } on RegionSelectionRequired catch (e) {
      setState(() {
        _regionOptions = e.allowedRegions;
        _selectedRegion ??= e.allowedRegions.isNotEmpty ? e.allowedRegions.first : null;
      });
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
                      // Only shown once /login comes back asking for a region -- a genuine
                      // multi-region account. Everyone else never sees this.
                      if (_regionOptions != null) ...[
                        Text('Choose a region to sign in with', style: Theme.of(context).textTheme.labelMedium),
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            for (final region in _regionOptions!) ...[
                              Expanded(child: _RegionPill(
                                label: _regionLabels[region] ?? region,
                                selected: _selectedRegion == region,
                                onTap: () => setState(() => _selectedRegion = region),
                              )),
                              if (region != _regionOptions!.last) const SizedBox(width: 10),
                            ],
                          ],
                        ),
                        const SizedBox(height: 20),
                      ],
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
                            icon: Icon(_obscurePassword ? PhosphorIcons.eyeSlash() : PhosphorIcons.eye()),
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
                      // Debug-only: never ships in a release build (flutter build --release / --profile),
                      // so a real APK handed to actual users never exposes these credentials.
                      if (kDebugMode) ...[
                        const SizedBox(height: 20),
                        DropdownButtonFormField<int>(
                          decoration: InputDecoration(
                            labelText: 'Dev account',
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                          ),
                          hint: const Text('Select a dev account'),
                          value: null,
                          items: [
                            for (var i = 0; i < _demoAccounts.length; i++)
                              DropdownMenuItem(
                                value: i,
                                child: Text(
                                  '${_demoAccounts[i].$1} — ${_demoAccounts[i].$3}',
                                  style: const TextStyle(fontSize: 13),
                                ),
                              ),
                          ],
                          onChanged: (i) {
                            if (i == null) return;
                            setState(() {
                              _userCtrl.text = _demoAccounts[i].$1;
                              _passCtrl.text = _demoAccounts[i].$2;
                            });
                          },
                        ),
                      ],
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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/enums.dart';
import '../../routing/role_routes.dart';
import '../authentication/auth_controller.dart';
import '../claims/capture_receipt_sheet.dart';

/// Legacy home (app now opens on My claims + bottom nav). Kept for reference.
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final user = auth.user;

    return Scaffold(
      appBar: AppBar(title: const Text('Expense Receipt')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(
            'Hello, ${user?.displayName ?? 'Salesman'}',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
          ),
          const SizedBox(height: 24),
          ListTile(
            title: const Text('My claims'),
            onTap: () => context.go('/claims'),
          ),
          ListTile(
            title: const Text('Add receipt'),
            onTap: () => showCaptureReceiptSheet(context, ref),
          ),
          ListTile(
            title: const Text('Profile'),
            onTap: () => context.go('/profile'),
          ),
          if (UserRoleX.fromJson(user?.role).isApprover)
            ListTile(
              title: const Text('Approvals'),
              onTap: () => context.push(homeRouteFor(UserRoleX.fromJson(user?.role))),
            ),
        ],
      ),
    );
  }
}

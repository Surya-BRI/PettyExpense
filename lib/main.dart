import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'src/api/api_config.dart';
import 'src/routing/app_router.dart';
import 'src/theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await dotenv.load(fileName: '.env');
  } catch (_) {
    // Fallback if asset missing; api_config still has platform defaults
  }
  debugPrint('API_BASE_URL=${resolveApiBase()}');
  runApp(const ProviderScope(child: ExpenseApp()));
}

class ExpenseApp extends ConsumerWidget {
  const ExpenseApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    return MaterialApp.router(
      title: 'Expense Receipt',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      routerConfig: router,
    );
  }
}

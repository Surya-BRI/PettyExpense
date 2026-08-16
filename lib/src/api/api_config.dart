import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Production backend — the fallback whenever nothing more specific is configured.
const String kProdApiBase = 'https://expensetracker-api.app-brisigns.com';

/// Resolve backend URL for the running platform.
///
/// Priority:
/// 1. `--dart-define=API_BASE_URL=...`
/// 2. Flutter root `.env` → `API_BASE_URL` (defaults to the prod backend there;
///    edit `.env` to point at a dev backend instead — see its top comments)
/// 3. [kProdApiBase] if `.env` is missing entirely (e.g. asset not bundled) —
///    the fallback must still be production, never a localhost/emulator address.
String resolveApiBase() {
  const fromDefine = String.fromEnvironment('API_BASE_URL');
  if (fromDefine.isNotEmpty) return fromDefine.trim();

  final fromEnv = dotenv.maybeGet('API_BASE_URL')?.trim();
  if (fromEnv != null && fromEnv.isNotEmpty) return fromEnv;

  return kProdApiBase;
}

import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Resolve backend URL for the running platform.
///
/// Priority:
/// 1. `--dart-define=API_BASE_URL=...`
/// 2. Flutter root `.env` → `API_BASE_URL`
/// 3. Platform default (Android emulator → 10.0.2.2, else 127.0.0.1)
String resolveApiBase() {
  const fromDefine = String.fromEnvironment('API_BASE_URL');
  if (fromDefine.isNotEmpty) return fromDefine.trim();

  final fromEnv = dotenv.maybeGet('API_BASE_URL')?.trim();
  if (fromEnv != null && fromEnv.isNotEmpty) return fromEnv;

  if (!kIsWeb && Platform.isAndroid) {
    return 'http://10.0.2.2:8000';
  }
  return 'http://127.0.0.1:8000';
}

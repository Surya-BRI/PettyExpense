// Auto-capture keep/discard decision and the remembered Manual/Auto choice. No doclens
// import: the screen hands over a file path, this decides.
import 'dart:io';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:image/image.dart' as img;

import 'capture_quality_gate.dart';
import 'models.dart';

/// Longest side the photo is shrunk to before the blur/glare check -- plenty for block
/// statistics and keeps the check well under a second on a phone.
const int kQualityCheckMaxSide = 1200;

/// Runs the blur/glare gate on a photo file. Top-level and synchronous so it can run on a
/// background isolate via `compute`. An unreadable file passes (the user still reviews
/// every photo, and a decode hiccup must not block capture).
QualityResult qualityOfImageFile(String path) {
  img.Image? decoded;
  try {
    decoded = img.decodeImage(File(path).readAsBytesSync());
  } catch (_) {
    decoded = null; // corrupt/truncated file: the decoder throws rather than returning null
  }
  if (decoded == null) return const QualityResult.pass();
  final longest = decoded.width > decoded.height ? decoded.width : decoded.height;
  final image = longest > kQualityCheckMaxSide
      ? img.copyResize(
          decoded,
          width: decoded.width >= decoded.height ? kQualityCheckMaxSide : null,
          height: decoded.height > decoded.width ? kQualityCheckMaxSide : null,
        )
      : decoded;
  return const CaptureQualityGate().evaluate(image);
}

/// Remembers whether the user prefers Auto capture. Manual is the default (Spec 5.1: the
/// camera never shoots by itself unless the user chose auto).
class CaptureModePrefs {
  CaptureModePrefs({FlutterSecureStorage? storage}) : _storage = storage ?? const FlutterSecureStorage();

  static const _key = 'capture_auto_mode';
  final FlutterSecureStorage _storage;

  Future<bool> loadAuto() async {
    try {
      return await _storage.read(key: _key) == 'true';
    } catch (_) {
      return false;
    }
  }

  Future<void> saveAuto(bool auto) async {
    try {
      await _storage.write(key: _key, value: auto ? 'true' : 'false');
    } catch (_) {}
  }
}

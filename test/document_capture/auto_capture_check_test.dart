// Auto-capture keeps a shot only if it passes the blur/glare gate; Manual is the default.
import 'dart:io';
import 'dart:math';

import 'package:expense_app/src/services/document_capture/auto_capture_check.dart';
import 'package:expense_app/src/services/document_capture/models.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;

/// PNG (lossless) so the pixel statistics the gate measures survive the round trip.
String _write(Directory dir, String name, img.Image image) {
  final file = File('${dir.path}/$name.png')..writeAsBytesSync(img.encodePng(image));
  return file.path;
}

/// Receipt-like: dark "text" specks on paper everywhere -> strong local contrast.
img.Image _sharpReceipt(int w, int h) {
  final rnd = Random(1);
  final image = img.Image(width: w, height: h);
  for (var y = 0; y < h; y++) {
    for (var x = 0; x < w; x++) {
      final v = rnd.nextDouble() < 0.25 ? 20 : 235;
      image.setPixelRgb(x, y, v, v, v);
    }
  }
  return image;
}

void main() {
  late Directory dir;
  setUp(() => dir = Directory.systemTemp.createTempSync('autocap'));
  tearDown(() => dir.deleteSync(recursive: true));

  test('a sharp receipt-like photo is kept', () {
    expect(qualityOfImageFile(_write(dir, 'sharp', _sharpReceipt(400, 600))).passes, isTrue);
  });

  test('a blurry (flat) photo is rejected as blurry', () {
    final flat = img.Image(width: 400, height: 600);
    img.fill(flat, color: img.ColorRgb8(128, 128, 128));
    final result = qualityOfImageFile(_write(dir, 'flat', flat));
    expect(result.passes, isFalse);
    expect(result.reason, CaptureBlockReason.blurry);
  });

  test('a mostly blown-out photo is rejected as glare', () {
    // Left 70%: pure white, no texture (specular hotspot). Right 30%: readable text.
    final image = _sharpReceipt(400, 600);
    for (var y = 0; y < 600; y++) {
      for (var x = 0; x < 280; x++) {
        image.setPixelRgb(x, y, 255, 255, 255);
      }
    }
    final result = qualityOfImageFile(_write(dir, 'glare', image));
    expect(result.passes, isFalse);
    expect(result.reason, CaptureBlockReason.glare);
  });

  test('a large photo is shrunk first and still judged', () {
    expect(qualityOfImageFile(_write(dir, 'big', _sharpReceipt(2400, 3200))).passes, isTrue);
  });

  test('an unreadable file never blocks capture', () {
    final path = '${dir.path}/broken.jpg';
    File(path).writeAsBytesSync([0, 1, 2, 3]);
    expect(qualityOfImageFile(path).passes, isTrue);
  });

  test('Manual is the default; Auto is remembered once chosen', () async {
    FlutterSecureStorage.setMockInitialValues({});
    final prefs = CaptureModePrefs();
    expect(await prefs.loadAuto(), isFalse);
    await prefs.saveAuto(true);
    expect(await CaptureModePrefs().loadAuto(), isTrue);
    await prefs.saveAuto(false);
    expect(await CaptureModePrefs().loadAuto(), isFalse);
  });
}

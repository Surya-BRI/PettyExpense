import 'package:expense_app/src/services/document_capture/capture_quality_gate.dart';
import 'package:expense_app/src/services/document_capture/models.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;

// A checkerboard of black/white pixels simulates printed text: strong local
// contrast everywhere, which is what real receipt text (even on bright
// thermal paper) looks like to a block-variance sharpness/glare check.
img.Image _texturedImage(int width, int height, {int lightValue = 250, int darkValue = 40}) {
  final image = img.Image(width: width, height: height);
  for (var y = 0; y < height; y++) {
    for (var x = 0; x < width; x++) {
      final isDark = (x ~/ 3 + y ~/ 3) % 2 == 0;
      final v = isDark ? darkValue : lightValue;
      image.setPixelRgb(x, y, v, v, v);
    }
  }
  return image;
}

img.Image _uniformImage(int width, int height, int value) {
  final image = img.Image(width: width, height: height);
  for (var y = 0; y < height; y++) {
    for (var x = 0; x < width; x++) {
      image.setPixelRgb(x, y, value, value, value);
    }
  }
  return image;
}

// A textured (text-like) image with a flat, blown-out rectangular patch
// covering the given fraction of the height, simulating a specular hotspot.
img.Image _withHotspot(int width, int height, double hotspotHeightFraction) {
  final image = _texturedImage(width, height);
  final hotspotRows = (height * hotspotHeightFraction).round();
  for (var y = 0; y < hotspotRows; y++) {
    for (var x = 0; x < width; x++) {
      image.setPixelRgb(x, y, 255, 255, 255);
    }
  }
  return image;
}

void main() {
  const gate = CaptureQualityGate();

  test('uniform bright white thermal paper (no printed text in this block set) is not treated as blur or glare on its own -- covers less than the severity threshold', () {
    // Mostly textured (like printed) with only a small uniform bright margin --
    // representative of a receipt with a normal blank header/footer strip.
    final image = _withHotspot(120, 120, 0.10);
    final result = gate.evaluate(image);
    expect(result.passes, isTrue);
  });

  test('fully textured receipt-like image (text-like contrast everywhere) passes cleanly', () {
    final image = _texturedImage(120, 120);
    final result = gate.evaluate(image);
    expect(result.passes, isTrue);
  });

  test('a large blown-out flat hotspot covering most of the frame blocks for glare, not for looking sharp elsewhere', () {
    final image = _withHotspot(120, 120, 0.60);
    final result = gate.evaluate(image);
    expect(result.passes, isFalse);
    expect(result.reason, CaptureBlockReason.glare);
  });

  test('a uniformly bright, low-contrast image (no text visible anywhere) blocks as blurry before it even reaches the glare check', () {
    final image = _uniformImage(120, 120, 250);
    final result = gate.evaluate(image);
    expect(result.passes, isFalse);
    expect(result.reason, CaptureBlockReason.blurry);
  });

  test('a uniformly dim, low-contrast image also blocks as blurry -- flatness alone is disqualifying regardless of brightness', () {
    final image = _uniformImage(120, 120, 90);
    final result = gate.evaluate(image);
    expect(result.passes, isFalse);
    expect(result.reason, CaptureBlockReason.blurry);
  });

  test('glare severity threshold is respected -- a small hotspot under the area fraction does not block', () {
    final image = _withHotspot(120, 120, 0.15);
    final result = gate.evaluate(image);
    expect(result.passes, isTrue);
  });

  test('glare severity threshold -- a hotspot just over the configured fraction does block', () {
    const thresholds = QualityThresholds(glareAreaFraction: 0.20);
    const strictGate = CaptureQualityGate(thresholds: thresholds);
    final image = _withHotspot(120, 120, 0.30);
    final result = strictGate.evaluate(image);
    expect(result.passes, isFalse);
    expect(result.reason, CaptureBlockReason.glare);
  });

  test('an empty/degenerate crop passes rather than crashing', () {
    final image = img.Image(width: 1, height: 1);
    final result = gate.evaluate(image);
    expect(result.passes, isTrue);
  });
}

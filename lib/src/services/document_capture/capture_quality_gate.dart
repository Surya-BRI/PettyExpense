import 'package:image/image.dart' as img;

import 'models.dart';

class QualityThresholds {
  const QualityThresholds({
    this.minSharpness = 4.0,
    this.glareBrightnessThreshold = 248,
    this.glareFlatnessThreshold = 6.0,
    this.glareAreaFraction = 0.25,
    this.gridDivisions = 12,
  });

  /// Below this average local-variance score, the crop is treated as blurry.
  /// Printed receipt text produces strong local contrast everywhere it
  /// appears; a genuinely blurry photo washes that out uniformly.
  final double minSharpness;

  /// Luminance (0-255) a block's mean must reach before it can even be
  /// considered for glare -- well above typical white thermal paper under
  /// normal light, which measures bright but rarely fully blown out.
  final double glareBrightnessThreshold;

  /// A block only counts as glare if it is ALSO this flat (low local
  /// variance) -- this is what tells a blown-out specular hotspot (no
  /// texture left) apart from bright-but-readable paper (text still creates
  /// local contrast even on white thermal stock).
  final double glareFlatnessThreshold;

  /// Fraction of the crop that must be bright-and-flat before glare actually
  /// blocks the capture. Deliberately high -- "block only when severe".
  final double glareAreaFraction;

  /// The crop is analyzed in gridDivisions x gridDivisions blocks.
  final int gridDivisions;
}

class CaptureQualityGate {
  const CaptureQualityGate({this.thresholds = const QualityThresholds()});

  final QualityThresholds thresholds;

  /// crop must already be warped/cropped to the detected document quad --
  /// this never looks at pixels outside it.
  QualityResult evaluate(img.Image crop) {
    final blocks = _blockStats(crop);
    if (blocks.isEmpty) return const QualityResult.pass();

    final avgVariance = blocks.map((b) => b.variance).reduce((a, b) => a + b) / blocks.length;
    if (avgVariance < thresholds.minSharpness) {
      return const QualityResult.block(CaptureBlockReason.blurry);
    }

    final glareBlocks = blocks.where(
      (b) => b.mean >= thresholds.glareBrightnessThreshold && b.variance <= thresholds.glareFlatnessThreshold,
    );
    final glareFraction = glareBlocks.length / blocks.length;
    if (glareFraction > thresholds.glareAreaFraction) {
      return const QualityResult.block(CaptureBlockReason.glare);
    }

    return const QualityResult.pass();
  }

  List<_BlockStats> _blockStats(img.Image image) {
    final cols = thresholds.gridDivisions;
    final rows = thresholds.gridDivisions;
    final blockWidth = (image.width / cols).floor();
    final blockHeight = (image.height / rows).floor();
    if (blockWidth < 1 || blockHeight < 1) return const [];

    final stats = <_BlockStats>[];
    for (var by = 0; by < rows; by++) {
      final y0 = by * blockHeight;
      final y1 = (by == rows - 1) ? image.height : y0 + blockHeight;
      for (var bx = 0; bx < cols; bx++) {
        final x0 = bx * blockWidth;
        final x1 = (bx == cols - 1) ? image.width : x0 + blockWidth;
        stats.add(_statsFor(image, x0, y0, x1, y1));
      }
    }
    return stats;
  }

  _BlockStats _statsFor(img.Image image, int x0, int y0, int x1, int y1) {
    var sum = 0.0;
    var sumSq = 0.0;
    var count = 0;
    for (var y = y0; y < y1; y++) {
      for (var x = x0; x < x1; x++) {
        final lum = image.getPixel(x, y).luminance.toDouble();
        sum += lum;
        sumSq += lum * lum;
        count++;
      }
    }
    if (count == 0) return const _BlockStats(mean: 0, variance: 0);
    final mean = sum / count;
    final variance = (sumSq / count) - (mean * mean);
    return _BlockStats(mean: mean, variance: variance < 0 ? 0 : variance);
  }
}

class _BlockStats {
  const _BlockStats({required this.mean, required this.variance});
  final double mean;
  final double variance;
}

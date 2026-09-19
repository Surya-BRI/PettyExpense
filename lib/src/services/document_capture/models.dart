// Platform-independent types for guided document capture. Nothing in this file
// touches doclens or any camera plugin -- that coupling lives only in the
// service implementation that wraps a specific package.
import 'dart:math' as math;

/// A point in whatever pixel space the caller is working in (raw frame or crop).
class CapturePoint {
  const CapturePoint(this.x, this.y);
  final double x;
  final double y;
}

/// The four corners of a detected document, in reading order (TL, TR, BR, BL).
class Quad {
  const Quad({
    required this.topLeft,
    required this.topRight,
    required this.bottomRight,
    required this.bottomLeft,
  });

  final CapturePoint topLeft;
  final CapturePoint topRight;
  final CapturePoint bottomRight;
  final CapturePoint bottomLeft;

  double _dist(CapturePoint a, CapturePoint b) {
    final dx = a.x - b.x;
    final dy = a.y - b.y;
    return math.sqrt(dx * dx + dy * dy);
  }

  double get _topWidth => _dist(topLeft, topRight);
  double get _bottomWidth => _dist(bottomLeft, bottomRight);
  double get _leftHeight => _dist(topLeft, bottomLeft);
  double get _rightHeight => _dist(topRight, bottomRight);

  double get width => (_topWidth + _bottomWidth) / 2;
  double get height => (_leftHeight + _rightHeight) / 2;

  /// Always >= 1 -- the ratio of the longer side to the shorter side, regardless
  /// of whether the document is held portrait or landscape.
  double get aspectRatio {
    final w = width;
    final h = height;
    if (w <= 0 || h <= 0) return 1.0;
    return w >= h ? w / h : h / w;
  }
}

/// Mirrors doclens' DetectionStatus so the state machine never imports doclens
/// directly -- the doclens-specific service translates into this.
enum DetectionStatus { searching, tooFar, tooClose, tilted, aligned, confirming, noPaper }

class DetectionTick {
  const DetectionTick({required this.timestamp, required this.status, this.quad});
  final DateTime timestamp;
  final DetectionStatus status;
  final Quad? quad;
}

/// The coarse, at-a-glance outline treatment the overlay draws.
enum GuidanceState { notFound, partial, aligned, confirming }

enum CaptureBlockReason { notFound, tooFar, tooClose, tilted, multipleItems, blurry, glare }

String messageForBlockReason(CaptureBlockReason reason) {
  switch (reason) {
    case CaptureBlockReason.notFound:
      return 'Whole receipt not visible';
    case CaptureBlockReason.tooFar:
      return 'Move closer';
    case CaptureBlockReason.tooClose:
      return 'Move back';
    case CaptureBlockReason.tilted:
      return 'Hold steady';
    case CaptureBlockReason.multipleItems:
      return 'Keep only one receipt in the frame';
    case CaptureBlockReason.blurry:
      return 'Hold steady';
    case CaptureBlockReason.glare:
      return 'Too much glare';
  }
}

class DocumentGuidance {
  const DocumentGuidance({
    required this.state,
    this.reason,
    this.quad,
    this.manualOverrideAvailable = false,
    this.readyForQualityCheck = false,
  });

  final GuidanceState state;
  final CaptureBlockReason? reason;
  final Quad? quad;

  /// True once guidance has been failing continuously long enough that the
  /// user should be allowed to shoot anyway rather than stay stuck.
  final bool manualOverrideAvailable;

  /// True exactly on the tick where the stability window has just elapsed --
  /// the caller should now sample a still frame and run the quality gate.
  final bool readyForQualityCheck;

  String? get message => reason == null ? null : messageForBlockReason(reason!);
}

class CaptureTuning {
  const CaptureTuning({
    this.stabilityWindow = const Duration(milliseconds: 1000),
    this.manualOverrideTimeout = const Duration(seconds: 9),
    this.maxAspectRatio = 8.0,
  });

  /// How long the document must stay aligned + passing quality before
  /// auto-capture fires. Product spec allows 800-1200ms; default sits in the middle.
  final Duration stabilityWindow;

  /// How long guidance can fail continuously before the shutter unblocks anyway.
  final Duration manualOverrideTimeout;

  /// Receipts are long and narrow -- allow up to this ratio before treating the
  /// quad as implausible (most likely two items in frame, not one receipt).
  final double maxAspectRatio;
}

class QualityResult {
  const QualityResult.pass()
      : passes = true,
        reason = null;
  const QualityResult.block(CaptureBlockReason this.reason) : passes = false;

  final bool passes;
  final CaptureBlockReason? reason;
}

/// What onQualityResult tells the caller to do next.
class CaptureDecision {
  const CaptureDecision({required this.shouldCapture, required this.guidance});
  final bool shouldCapture;
  final DocumentGuidance guidance;
}

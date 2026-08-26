import 'models.dart';

/// Pure decision logic for guided capture -- no camera, no doclens, no timers
/// of its own. The caller drives it with a DetectionTick per frame (real
/// timestamps in production, synthetic ones in tests) and, once
/// readyForQualityCheck fires, a QualityResult from a separate quality gate.
class CaptureStateMachine {
  CaptureStateMachine({this.tuning = const CaptureTuning()});

  final CaptureTuning tuning;

  DateTime? _streakStart;
  DateTime? _badStreakStart;

  bool _isGeometryGood(DetectionTick tick) {
    if (tick.status != DetectionStatus.aligned && tick.status != DetectionStatus.confirming) {
      return false;
    }
    final quad = tick.quad;
    if (quad == null) return false;
    return quad.aspectRatio <= tuning.maxAspectRatio;
  }

  CaptureBlockReason _reasonFor(DetectionTick tick) {
    final quad = tick.quad;
    if (quad != null && quad.aspectRatio > tuning.maxAspectRatio) {
      return CaptureBlockReason.multipleItems;
    }
    switch (tick.status) {
      case DetectionStatus.searching:
      case DetectionStatus.noPaper:
        return CaptureBlockReason.notFound;
      case DetectionStatus.tooFar:
        return CaptureBlockReason.tooFar;
      case DetectionStatus.tooClose:
        return CaptureBlockReason.tooClose;
      case DetectionStatus.tilted:
        return CaptureBlockReason.tilted;
      case DetectionStatus.aligned:
      case DetectionStatus.confirming:
        return CaptureBlockReason.notFound;
    }
  }

  /// Feed one detection frame in. Returns the guidance the overlay should show.
  DocumentGuidance onTick(DetectionTick tick) {
    if (!_isGeometryGood(tick)) {
      _streakStart = null;
      _badStreakStart ??= tick.timestamp;
      final overrideAvailable =
          tick.timestamp.difference(_badStreakStart!) >= tuning.manualOverrideTimeout;
      final isNotFound = tick.quad == null ||
          tick.status == DetectionStatus.searching ||
          tick.status == DetectionStatus.noPaper;
      return DocumentGuidance(
        state: isNotFound ? GuidanceState.notFound : GuidanceState.partial,
        reason: _reasonFor(tick),
        quad: tick.quad,
        manualOverrideAvailable: overrideAvailable,
      );
    }

    _badStreakStart = null;
    final streakStart = _streakStart ??= tick.timestamp;
    final elapsed = tick.timestamp.difference(streakStart);

    if (elapsed >= tuning.stabilityWindow) {
      return DocumentGuidance(state: GuidanceState.confirming, quad: tick.quad, readyForQualityCheck: true);
    }
    final isFirstGoodTick = elapsed == Duration.zero;
    return DocumentGuidance(
      state: isFirstGoodTick ? GuidanceState.aligned : GuidanceState.confirming,
      quad: tick.quad,
    );
  }

  /// Called once after the caller has sampled a still frame and run the
  /// quality gate in response to readyForQualityCheck. A failing result
  /// aborts the stability streak -- the hold-still window must restart from
  /// scratch, it does not just pause.
  CaptureDecision onQualityResult(QualityResult result, DateTime now, {Quad? quad}) {
    if (result.passes) {
      return CaptureDecision(
        shouldCapture: true,
        guidance: DocumentGuidance(state: GuidanceState.confirming, quad: quad),
      );
    }
    _streakStart = null;
    return CaptureDecision(
      shouldCapture: false,
      guidance: DocumentGuidance(state: GuidanceState.partial, reason: result.reason, quad: quad),
    );
  }

  /// Call after a successful capture (or a user-initiated retake) so the next
  /// guidance cycle starts clean.
  void reset() {
    _streakStart = null;
    _badStreakStart = null;
  }
}

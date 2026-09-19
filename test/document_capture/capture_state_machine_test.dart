import 'package:expense_app/src/services/document_capture/capture_state_machine.dart';
import 'package:expense_app/src/services/document_capture/models.dart';
import 'package:flutter_test/flutter_test.dart';

final _epoch = DateTime(2026, 1, 1);

Quad _quad({double width = 400, double height = 200}) {
  return Quad(
    topLeft: const CapturePoint(0, 0),
    topRight: CapturePoint(width, 0),
    bottomRight: CapturePoint(width, height),
    bottomLeft: CapturePoint(0, height),
  );
}

DetectionTick _tick(Duration offset, DetectionStatus status, {Quad? quad}) {
  return DetectionTick(timestamp: _epoch.add(offset), status: status, quad: quad);
}

void main() {
  group('reason messages per detection status', () {
    final machine = CaptureStateMachine();

    test('searching and noPaper both read as not found, whole receipt not visible', () {
      final a = machine.onTick(_tick(Duration.zero, DetectionStatus.searching));
      expect(a.state, GuidanceState.notFound);
      expect(a.message, 'Whole receipt not visible');

      final b = machine.onTick(_tick(const Duration(milliseconds: 100), DetectionStatus.noPaper));
      expect(b.state, GuidanceState.notFound);
      expect(b.message, 'Whole receipt not visible');
    });

    test('tooFar means move closer', () {
      final g = machine.onTick(_tick(const Duration(milliseconds: 200), DetectionStatus.tooFar, quad: _quad()));
      expect(g.state, GuidanceState.partial);
      expect(g.message, 'Move closer');
    });

    test('tooClose means move back', () {
      final g = machine.onTick(_tick(const Duration(milliseconds: 300), DetectionStatus.tooClose, quad: _quad()));
      expect(g.message, 'Move back');
    });

    test('tilted means hold steady', () {
      final g = machine.onTick(_tick(const Duration(milliseconds: 400), DetectionStatus.tilted, quad: _quad()));
      expect(g.message, 'Hold steady');
    });
  });

  group('aspect ratio allowance', () {
    test('an 8:1 receipt is accepted as geometry-good, not flagged as multiple items', () {
      final machine = CaptureStateMachine();
      final quad = _quad(width: 800, height: 100); // 8:1
      final g = machine.onTick(_tick(Duration.zero, DetectionStatus.aligned, quad: quad));
      expect(g.state, GuidanceState.aligned);
      expect(g.reason, isNull);
    });

    test('a portrait 1:8 receipt (rotated) is equally accepted', () {
      final machine = CaptureStateMachine();
      final quad = _quad(width: 100, height: 800);
      final g = machine.onTick(_tick(Duration.zero, DetectionStatus.aligned, quad: quad));
      expect(g.state, GuidanceState.aligned);
    });

    test('beyond the 8:1 ceiling reads as multiple items, not aligned', () {
      final machine = CaptureStateMachine();
      final quad = _quad(width: 1000, height: 80); // 12.5:1
      final g = machine.onTick(_tick(Duration.zero, DetectionStatus.aligned, quad: quad));
      expect(g.state, GuidanceState.partial);
      expect(g.reason, CaptureBlockReason.multipleItems);
      expect(g.message, 'Keep only one receipt in the frame');
    });

    test('a card-shaped 1.6:1 quad is well within the allowance', () {
      final machine = CaptureStateMachine();
      final quad = _quad(width: 160, height: 100);
      final g = machine.onTick(_tick(Duration.zero, DetectionStatus.aligned, quad: quad));
      expect(g.state, GuidanceState.aligned);
    });
  });

  group('stability timer', () {
    test('stays aligned/confirming without reaching readyForQualityCheck before the window elapses', () {
      final machine = CaptureStateMachine(tuning: const CaptureTuning(stabilityWindow: Duration(milliseconds: 1000)));
      final quad = _quad();
      final first = machine.onTick(_tick(Duration.zero, DetectionStatus.aligned, quad: quad));
      expect(first.state, GuidanceState.aligned);
      expect(first.readyForQualityCheck, isFalse);

      final mid = machine.onTick(_tick(const Duration(milliseconds: 500), DetectionStatus.aligned, quad: quad));
      expect(mid.state, GuidanceState.confirming);
      expect(mid.readyForQualityCheck, isFalse);
    });

    test('fires readyForQualityCheck once the window has fully elapsed', () {
      final machine = CaptureStateMachine(tuning: const CaptureTuning(stabilityWindow: Duration(milliseconds: 1000)));
      final quad = _quad();
      machine.onTick(_tick(Duration.zero, DetectionStatus.aligned, quad: quad));
      final ready = machine.onTick(_tick(const Duration(milliseconds: 1000), DetectionStatus.aligned, quad: quad));
      expect(ready.state, GuidanceState.confirming);
      expect(ready.readyForQualityCheck, isTrue);
    });

    test('an interruption mid-window resets the streak -- it must restart from zero', () {
      final machine = CaptureStateMachine(tuning: const CaptureTuning(stabilityWindow: Duration(milliseconds: 1000)));
      final quad = _quad();
      machine.onTick(_tick(Duration.zero, DetectionStatus.aligned, quad: quad));
      machine.onTick(_tick(const Duration(milliseconds: 700), DetectionStatus.aligned, quad: quad));
      // interrupted by a tilt right before the window would have elapsed
      machine.onTick(_tick(const Duration(milliseconds: 800), DetectionStatus.tilted, quad: quad));
      // good again, but this must count as a brand new streak, not a resumed one
      final resumed = machine.onTick(_tick(const Duration(milliseconds: 850), DetectionStatus.aligned, quad: quad));
      expect(resumed.state, GuidanceState.aligned);
      expect(resumed.readyForQualityCheck, isFalse);
      final tooEarly = machine.onTick(_tick(const Duration(milliseconds: 1700), DetectionStatus.aligned, quad: quad));
      // only 850ms since the restart -- window (1000ms) has not elapsed yet
      expect(tooEarly.readyForQualityCheck, isFalse);
    });

    test('a failing quality result resets the streak just like a geometry interruption', () {
      final machine = CaptureStateMachine(tuning: const CaptureTuning(stabilityWindow: Duration(milliseconds: 1000)));
      final quad = _quad();
      machine.onTick(_tick(Duration.zero, DetectionStatus.aligned, quad: quad));
      final ready = machine.onTick(_tick(const Duration(milliseconds: 1000), DetectionStatus.aligned, quad: quad));
      expect(ready.readyForQualityCheck, isTrue);

      final decision = machine.onQualityResult(
        const QualityResult.block(CaptureBlockReason.glare),
        _epoch.add(const Duration(milliseconds: 1000)),
        quad: quad,
      );
      expect(decision.shouldCapture, isFalse);
      expect(decision.guidance.reason, CaptureBlockReason.glare);
      expect(decision.guidance.message, 'Too much glare');

      // next good tick must restart the window from zero -- the hold-still
      // window is abortable, not paused/resumed
      final afterReject = machine.onTick(_tick(const Duration(milliseconds: 1050), DetectionStatus.aligned, quad: quad));
      expect(afterReject.state, GuidanceState.aligned);
      expect(afterReject.readyForQualityCheck, isFalse);
    });

    test('a passing quality result tells the caller to capture', () {
      final machine = CaptureStateMachine();
      final quad = _quad();
      final decision = machine.onQualityResult(const QualityResult.pass(), _epoch, quad: quad);
      expect(decision.shouldCapture, isTrue);
    });
  });

  group('manual override timeout', () {
    test('is not available before the configured timeout', () {
      final machine = CaptureStateMachine(tuning: const CaptureTuning(manualOverrideTimeout: Duration(seconds: 9)));
      machine.onTick(_tick(Duration.zero, DetectionStatus.searching));
      final g = machine.onTick(_tick(const Duration(seconds: 8), DetectionStatus.searching));
      expect(g.manualOverrideAvailable, isFalse);
    });

    test('becomes available once continuous failure reaches the timeout', () {
      final machine = CaptureStateMachine(tuning: const CaptureTuning(manualOverrideTimeout: Duration(seconds: 9)));
      machine.onTick(_tick(Duration.zero, DetectionStatus.searching));
      final g = machine.onTick(_tick(const Duration(seconds: 9), DetectionStatus.tooFar, quad: _quad()));
      expect(g.manualOverrideAvailable, isTrue);
    });

    test('a single good frame in the middle resets the override countdown', () {
      final machine = CaptureStateMachine(tuning: const CaptureTuning(manualOverrideTimeout: Duration(seconds: 9)));
      machine.onTick(_tick(Duration.zero, DetectionStatus.searching));
      machine.onTick(_tick(const Duration(seconds: 5), DetectionStatus.searching));
      // briefly good -- does not count toward the failure streak
      machine.onTick(_tick(const Duration(seconds: 6), DetectionStatus.aligned, quad: _quad()));
      machine.onTick(_tick(const Duration(seconds: 6, milliseconds: 100), DetectionStatus.searching));
      final g = machine.onTick(_tick(const Duration(seconds: 14, milliseconds: 900), DetectionStatus.searching));
      // only ~8.8s of continuous failure since the reset at 6.1s
      expect(g.manualOverrideAvailable, isFalse);
    });
  });

  group('reset', () {
    test('clears an in-progress streak so guidance starts clean', () {
      final machine = CaptureStateMachine(tuning: const CaptureTuning(stabilityWindow: Duration(milliseconds: 1000)));
      final quad = _quad();
      machine.onTick(_tick(Duration.zero, DetectionStatus.aligned, quad: quad));
      machine.reset();
      final g = machine.onTick(_tick(const Duration(milliseconds: 1000), DetectionStatus.aligned, quad: quad));
      // if the old streak had survived, this would already be ready (1000ms elapsed) --
      // after reset it must be treated as a fresh first tick instead
      expect(g.readyForQualityCheck, isFalse);
      expect(g.state, GuidanceState.aligned);
    });
  });
}

// The one file in document_capture/ allowed to import doclens. Everything else
// (capture_state_machine.dart, capture_quality_gate.dart, models.dart) stays
// doclens-agnostic; this file is the translation boundary between doclens'
// types and this app's own DetectionStatus/Quad/CapturePoint.
import 'package:doclens/doclens.dart' as doclens;

import 'models.dart' as capture;

capture.DetectionStatus mapDetectionStatus(doclens.DetectionStatus status) {
  switch (status) {
    case doclens.DetectionStatus.searching:
      return capture.DetectionStatus.searching;
    case doclens.DetectionStatus.tooFar:
      return capture.DetectionStatus.tooFar;
    case doclens.DetectionStatus.tooClose:
      return capture.DetectionStatus.tooClose;
    case doclens.DetectionStatus.tilted:
      return capture.DetectionStatus.tilted;
    case doclens.DetectionStatus.aligned:
      return capture.DetectionStatus.aligned;
    case doclens.DetectionStatus.confirming:
      return capture.DetectionStatus.confirming;
    case doclens.DetectionStatus.noPaper:
      return capture.DetectionStatus.noPaper;
    case doclens.DetectionStatus.focusing:
      // Only ever emitted by doclens' own auto-capture focus-lock, which is
      // disabled here (capture is self-driven via CaptureStateMachine) -- kept
      // as a defensive mapping rather than assumed unreachable. "Hold steady"
      // is the closest existing guidance message.
      return capture.DetectionStatus.tilted;
  }
}

capture.Quad? mapQuad(doclens.Quad? quad) {
  if (quad == null) return null;
  return capture.Quad(
    topLeft: capture.CapturePoint(quad.topLeft.dx, quad.topLeft.dy),
    topRight: capture.CapturePoint(quad.topRight.dx, quad.topRight.dy),
    bottomRight: capture.CapturePoint(quad.bottomRight.dx, quad.bottomRight.dy),
    bottomLeft: capture.CapturePoint(quad.bottomLeft.dx, quad.bottomLeft.dy),
  );
}

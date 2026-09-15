import 'dart:async';
import 'dart:io';

import 'package:doclens/doclens.dart' as doclens;
import 'package:flutter/material.dart';
import 'package:image/image.dart' as img;

import '../../services/document_capture/capture_quality_gate.dart';
import '../../services/document_capture/capture_state_machine.dart';
import '../../services/document_capture/doclens_bridge.dart';
import '../../services/document_capture/models.dart' as capture;
import '../../theme/app_theme.dart';

/// What GuidedCaptureScreen hands back to whoever pushed it.
class GuidedCaptureResult {
  const GuidedCaptureResult.captured(String this.imagePath) : useFallback = false;
  const GuidedCaptureResult.fallback()
      : imagePath = null,
        useFallback = true;

  /// Path to the RAW, unwarped camera still -- never the cropped preview.
  /// The crop is only ever used on-screen and for the quality gate; the
  /// audit record in S3 must be the untouched original.
  final String? imagePath;

  /// True when the user gave up on guided capture and wants the old
  /// plain camera/gallery picker instead.
  final bool useFallback;
}

class GuidedCaptureScreen extends StatefulWidget {
  const GuidedCaptureScreen({super.key});

  @override
  State<GuidedCaptureScreen> createState() => _GuidedCaptureScreenState();
}

class _GuidedCaptureScreenState extends State<GuidedCaptureScreen> with WidgetsBindingObserver {
  late final doclens.DoclensController _controller;
  final _stateMachine = CaptureStateMachine();
  final _qualityGate = const CaptureQualityGate();

  StreamSubscription<doclens.DetectionStatus>? _statusSub;
  StreamSubscription<doclens.Quad?>? _quadSub;

  // Only ever read inside _onQuad, which fires on the same detection cycle as
  // the matching status update -- see doclens_bridge.dart for why a possible
  // one-frame staleness here doesn't matter (guidance, not the pass/fail gate).
  doclens.DetectionStatus _lastDoclensStatus = doclens.DetectionStatus.searching;

  capture.DocumentGuidance _guidance = const capture.DocumentGuidance(state: capture.GuidanceState.notFound);

  // True while a capture()+quality-check round trip is in flight -- incoming
  // ticks are ignored meanwhile so a slow native capture can't race a second
  // one, and so the state machine only ever sees one decision at a time.
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _controller = doclens.DoclensController(
      config: const doclens.ScannerConfig(
        // Self-driven: CaptureStateMachine + CaptureQualityGate decide when to
        // fire, not doclens' own auto-capture heuristic (which isn't tuned for
        // this app's long thermal-receipt shape).
        enableAutoCapture: false,
        enableLiveDetection: true,
        enableStabilityStatus: true,
        enablePerspectiveWarp: true,
        jpegQuality: 100,
      ),
    );
    unawaited(_init());
  }

  Future<void> _init() async {
    await _controller.initialize();
    if (!mounted) return;
    setState(() {});
    _statusSub = _controller.statusStream.listen((s) => _lastDoclensStatus = s);
    _quadSub = _controller.quadStream.listen(_onQuad);
  }

  void _onQuad(doclens.Quad? quad) {
    if (_busy) return;
    final mappedQuad = mapQuad(quad);
    final tick = capture.DetectionTick(
      timestamp: DateTime.now(),
      status: mapDetectionStatus(_lastDoclensStatus),
      quad: mappedQuad,
    );
    final guidance = _stateMachine.onTick(tick);
    if (!mounted) return;
    setState(() => _guidance = guidance);
    if (guidance.readyForQualityCheck) {
      unawaited(_runQualityCheckAndMaybeCapture(mappedQuad));
    }
  }

  Future<void> _runQualityCheckAndMaybeCapture(capture.Quad? quad) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await _controller.capture();
      final croppedPath = result.croppedImagePath;
      capture.QualityResult quality;
      if (croppedPath != null) {
        final decoded = img.decodeImage(await File(croppedPath).readAsBytes());
        // No decodable crop is a warp/IO glitch, not a quality problem with
        // the raw capture itself -- don't block the user on it.
        quality = decoded == null ? const capture.QualityResult.pass() : _qualityGate.evaluate(decoded);
      } else {
        quality = const capture.QualityResult.pass();
      }
      final decision = _stateMachine.onQualityResult(quality, DateTime.now(), quad: quad);
      if (!mounted) return;
      if (decision.shouldCapture) {
        _finish(result.rawImagePath);
        return;
      }
      setState(() => _guidance = decision.guidance);
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = 'Capture failed, hold steady and try again.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// Manual shutter tap -- only reachable while the button is enabled (good
  /// framing, or the manual-override timeout has elapsed). Always accepted
  /// outright, with no quality gate: this is the user's explicit decision,
  /// not the automatic guided path.
  Future<void> _manualCapture() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await _controller.capture();
      _finish(result.rawImagePath);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = 'Capture failed, try again.';
      });
    }
  }

  void _finish(String rawImagePath) {
    _stateMachine.reset();
    Navigator.of(context).pop(GuidedCaptureResult.captured(rawImagePath));
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (!_controller.isInitialized) return;
    if (state == AppLifecycleState.paused || state == AppLifecycleState.inactive) {
      unawaited(_controller.pause());
    } else if (state == AppLifecycleState.resumed) {
      unawaited(_controller.resume());
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _statusSub?.cancel();
    _quadSub?.cancel();
    _controller.dispose();
    super.dispose();
  }

  bool get _shutterEnabled =>
      !_busy &&
      (_guidance.state == capture.GuidanceState.aligned ||
          _guidance.state == capture.GuidanceState.confirming ||
          _guidance.manualOverrideAvailable);

  @override
  Widget build(BuildContext context) {
    if (!_controller.isInitialized) {
      return const Scaffold(
        backgroundColor: Colors.black,
        body: Center(child: CircularProgressIndicator(color: Colors.white)),
      );
    }
    final shutterEnabled = _shutterEnabled;
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          Positioned.fill(child: doclens.DoclensView(controller: _controller)),
          Positioned.fill(
            child: CustomPaint(painter: _QuadPainter(quad: _guidance.quad, state: _guidance.state)),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: IconButton(
                onPressed: () => Navigator.of(context).pop(),
                icon: const Icon(Icons.close, color: Colors.white),
              ),
            ),
          ),
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: SafeArea(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (_error != null) ...[
                      Text(_error!, style: const TextStyle(color: Colors.redAccent)),
                      const SizedBox(height: 8),
                    ] else if (_guidance.message != null) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                        decoration: BoxDecoration(
                          color: Colors.black.withValues(alpha: 0.6),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          _guidance.message!,
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],
                    GestureDetector(
                      onTap: shutterEnabled ? _manualCapture : null,
                      child: Container(
                        width: 72,
                        height: 72,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: shutterEnabled ? AppColors.orange : Colors.white24,
                          border: Border.all(color: Colors.white, width: 3),
                        ),
                        child: _busy
                            ? const Padding(
                                padding: EdgeInsets.all(20),
                                child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                              )
                            : null,
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextButton(
                      onPressed: () => Navigator.of(context).pop(const GuidedCaptureResult.fallback()),
                      child: const Text(
                        'Trouble scanning? Use camera instead',
                        style: TextStyle(color: Colors.white70),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Draws the live guidance quad -- doclens streams corners normalized to
/// [0,1] over the preview, so they scale directly to this painter's size as
/// long as it's stacked exactly over DoclensView (both Positioned.fill here).
class _QuadPainter extends CustomPainter {
  const _QuadPainter({required this.quad, required this.state});

  final capture.Quad? quad;
  final capture.GuidanceState state;

  @override
  void paint(Canvas canvas, Size size) {
    final q = quad;
    if (q == null) return;
    final color = switch (state) {
      capture.GuidanceState.aligned || capture.GuidanceState.confirming => Colors.greenAccent,
      capture.GuidanceState.partial => Colors.orangeAccent,
      capture.GuidanceState.notFound => Colors.white54,
    };
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3;
    final path = Path()
      ..moveTo(q.topLeft.x * size.width, q.topLeft.y * size.height)
      ..lineTo(q.topRight.x * size.width, q.topRight.y * size.height)
      ..lineTo(q.bottomRight.x * size.width, q.bottomRight.y * size.height)
      ..lineTo(q.bottomLeft.x * size.width, q.bottomLeft.y * size.height)
      ..close();
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant _QuadPainter oldDelegate) =>
      oldDelegate.quad != quad || oldDelegate.state != state;
}

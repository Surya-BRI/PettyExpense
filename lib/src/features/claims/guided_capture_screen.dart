import 'dart:async';
import 'dart:io';

import 'package:doclens/doclens.dart' as doclens;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../services/document_capture/capture_state_machine.dart';
import '../../services/document_capture/doclens_bridge.dart';
import '../../services/document_capture/models.dart' as capture;
import '../../theme/app_theme.dart';

void _log(String message) {
  if (kDebugMode) debugPrint('[guided-capture] $message');
}

/// What GuidedCaptureScreen hands back to whoever pushed it.
class GuidedCaptureResult {
  const GuidedCaptureResult.captured(String this.imagePath)
    : useFallback = false;
  const GuidedCaptureResult.fallback() : imagePath = null, useFallback = true;

  /// Path to the photo to upload: the perspective-corrected crop of just the receipt
  /// (background outside the detected outline removed) whenever the scanner found a
  /// usable outline, otherwise the full camera still so nothing is ever lost.
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

class _GuidedCaptureScreenState extends State<GuidedCaptureScreen>
    with WidgetsBindingObserver {
  late final doclens.DoclensController _controller;
  final _stateMachine = CaptureStateMachine();

  StreamSubscription<doclens.DetectionStatus>? _statusSub;
  StreamSubscription<doclens.Quad?>? _quadSub;

  // Only ever read inside _onQuad, which fires on the same detection cycle as
  // the matching status update -- see doclens_bridge.dart for why a possible
  // one-frame staleness here doesn't matter (guidance, not the pass/fail gate).
  doclens.DetectionStatus _lastDoclensStatus =
      doclens.DetectionStatus.searching;

  capture.DocumentGuidance _guidance = const capture.DocumentGuidance(
    state: capture.GuidanceState.notFound,
  );

  // True while a capture is in flight, so a second tap can't race the first.
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _controller = doclens.DoclensController(
      config: const doclens.ScannerConfig(
        // Photos are only ever taken when the user taps the shutter. Live detection
        // stays on purely to draw the outline and show framing hints.
        enableAutoCapture: false,
        enableLiveDetection: true,
        enableStabilityStatus: true,
        // Crop to the detected outline and flatten it, then turn it upright so the
        // uploaded image (and OCR) sees only the receipt, not the desk around it.
        enablePerspectiveWarp: true,
        autoOrientation: doclens.AutoOrientation.auto,
        // Visually identical to 100 and ~3x smaller to upload.
        jpegQuality: 92,
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
  }

  /// The only way a photo is taken: the user taps the shutter. Always available
  /// (the outline and hints are guidance, never a gate) and accepted outright.
  Future<void> _capture() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    // Snapshot the framing at the moment of the tap -- that is the outline the crop uses.
    final framing = _guidance;
    final doclens.ScanResult result;
    try {
      result = await _controller.capture();
    } catch (e) {
      _log('capture failed: $e');
      if (!mounted) return;
      setState(() {
        _busy = false;
        _error = 'Capture failed, try again.';
      });
      return;
    }
    if (!mounted) return;

    // Auto-detection can lock onto the wrong lines (e.g. a table border when the paper is
    // wider than the frame), so the user always checks the crop before it is used.
    unawaited(_controller.pause());
    final chosen = await Navigator.of(context).push<String>(
      MaterialPageRoute(
        fullscreenDialog: true,
        builder: (_) => _CaptureReviewScreen(
          controller: _controller,
          result: result,
          cropUsable: _cropUsable(result, framing),
        ),
      ),
    );
    if (!mounted) return;
    if (chosen != null) {
      _finish(chosen);
      return;
    }
    // Retake: back to the live camera with a clean slate.
    _stateMachine.reset();
    unawaited(_controller.resume());
    setState(() {
      _busy = false;
      _guidance = const capture.DocumentGuidance(
        state: capture.GuidanceState.notFound,
      );
    });
  }

  /// The auto crop is only offered when there was a real, plausible outline on screen at
  /// the tap: no outline, an implausible one (two items side by side), or a failed warp
  /// would produce a wrong crop, so the review screen starts from the full photo instead.
  bool _cropUsable(
    doclens.ScanResult result,
    capture.DocumentGuidance framing,
  ) {
    final usable =
        result.croppedImagePath != null &&
        result.warpError == null &&
        framing.quad != null &&
        framing.reason != capture.CaptureBlockReason.multipleItems;
    _log(
      'crop ${usable ? 'offered' : 'not offered'} (cropped=${result.croppedImagePath != null}, '
      'warpError=${result.warpError}, outline=${framing.quad != null}, reason=${framing.reason?.name})',
    );
    return usable;
  }

  void _finish(String imagePath) {
    _stateMachine.reset();
    Navigator.of(context).pop(GuidedCaptureResult.captured(imagePath));
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (!_controller.isInitialized) return;
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.inactive) {
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

  bool get _wellFramed =>
      _guidance.state == capture.GuidanceState.aligned ||
      _guidance.state == capture.GuidanceState.confirming;

  /// Framing hints ("Move closer", "Hold steady") come from the guidance; when the
  /// receipt is well framed, prompt the user to take the photo themselves.
  String? get _statusMessage {
    if (_busy) return 'Taking photo…';
    if (_wellFramed) return 'Looks good, tap the button to take the photo';
    return _guidance.message ??
        'Fit the whole receipt in the frame, then tap the button';
  }

  @override
  Widget build(BuildContext context) {
    if (!_controller.isInitialized) {
      return const Scaffold(
        backgroundColor: Colors.black,
        body: Center(child: CircularProgressIndicator(color: Colors.white)),
      );
    }
    return Scaffold(
      backgroundColor: Colors.black,
      // StackFit.expand + every child positioned: the Stack must fill the whole screen. A
      // non-positioned child (the close button used to be one) makes a loose Stack shrink to
      // that child's size, squashing the camera preview and overlay into a tiny corner box.
      body: Stack(
        fit: StackFit.expand,
        children: [
          Positioned.fill(child: doclens.DoclensView(controller: _controller)),
          Positioned.fill(
            child: CustomPaint(
              painter: _QuadPainter(
                quad: _guidance.quad,
                state: _guidance.state,
              ),
            ),
          ),
          Positioned(
            top: 0,
            left: 0,
            child: SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(8),
                child: IconButton(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.close, color: Colors.white),
                ),
              ),
            ),
          ),
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: SafeArea(
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 24,
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (_error != null) ...[
                      Text(
                        _error!,
                        style: const TextStyle(color: Colors.redAccent),
                      ),
                      const SizedBox(height: 8),
                    ] else if (_statusMessage != null) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 14,
                          vertical: 8,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.black.withValues(alpha: 0.6),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          _statusMessage!,
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],
                    // Always tappable; a green ring shows the receipt is well framed.
                    Semantics(
                      button: true,
                      label: 'Take photo',
                      child: GestureDetector(
                        onTap: _busy ? null : _capture,
                        child: Container(
                          width: 76,
                          height: 76,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: AppColors.orange,
                            border: Border.all(
                              color: _wellFramed
                                  ? Colors.greenAccent
                                  : Colors.white,
                              width: 4,
                            ),
                          ),
                          child: _busy
                              ? const Padding(
                                  padding: EdgeInsets.all(20),
                                  child: CircularProgressIndicator(
                                    color: Colors.white,
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(
                                  Icons.photo_camera,
                                  color: Colors.white,
                                  size: 30,
                                ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextButton(
                      onPressed: () => Navigator.of(
                        context,
                      ).pop(const GuidedCaptureResult.fallback()),
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
      capture.GuidanceState.aligned ||
      capture.GuidanceState.confirming => Colors.greenAccent,
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

/// Shown right after the shutter: the user confirms the crop, fixes it by dragging the
/// corners, falls back to the full photo, or retakes. Pops with the image path to upload,
/// or null to retake.
class _CaptureReviewScreen extends StatefulWidget {
  const _CaptureReviewScreen({
    required this.controller,
    required this.result,
    required this.cropUsable,
  });

  final doclens.DoclensController controller;
  final doclens.ScanResult result;
  final bool cropUsable;

  @override
  State<_CaptureReviewScreen> createState() => _CaptureReviewScreenState();
}

class _CaptureReviewScreenState extends State<_CaptureReviewScreen> {
  late String _path;
  late bool _cropped;
  doclens.Quad? _quad;

  @override
  void initState() {
    super.initState();
    _cropped = widget.cropUsable;
    _path = _cropped
        ? widget.result.croppedImagePath!
        : widget.result.rawImagePath;
    _quad = widget.result.detectedQuad;
  }

  Future<void> _adjustCorners() async {
    final raw = widget.result.rawImagePath;
    doclens.Quad? saved;
    final newPath = await Navigator.of(context).push<String>(
      MaterialPageRoute(
        builder: (_) => doclens.EditCornersScreen(
          imagePath: raw,
          initialQuad: _quad ?? widget.result.detectedQuad,
          imageSize: widget.result.rawImageSize,
          title: 'Drag the corners to the paper edges',
          saveLabel: 'Crop',
          onSave: (quad) {
            saved = quad;
            return widget.controller.warpImage(raw, quad);
          },
        ),
      ),
    );
    if (!mounted || newPath == null) return;
    setState(() {
      _path = newPath;
      _cropped = true;
      _quad = saved ?? _quad;
    });
  }

  void _useFullPhoto() => setState(() {
    _path = widget.result.rawImagePath;
    _cropped = false;
  });

  @override
  Widget build(BuildContext context) {
    final hint = _cropped
        ? 'Check that all four edges of the receipt are inside the crop.'
        : widget.cropUsable
        ? 'Showing the full photo.'
        : 'The receipt edges were not found, so this is the full photo. Use “Adjust corners” to crop it.';
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(8, 4, 16, 4),
              child: Row(
                children: [
                  IconButton(
                    tooltip: 'Retake',
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.arrow_back, color: Colors.white),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    _cropped ? 'Check the crop' : 'Check the photo',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: InteractiveViewer(
                minScale: 1,
                maxScale: 5,
                child: Center(
                  child: Image.file(
                    File(_path),
                    key: ValueKey(_path),
                    fit: BoxFit.contain,
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 4),
              child: Text(
                hint,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white70, height: 1.35),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => Navigator.of(context).pop(),
                      icon: const Icon(Icons.refresh),
                      label: const Text('Retake'),
                      style: _outlinedOnDark,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _adjustCorners,
                      icon: const Icon(Icons.crop),
                      label: const Text('Adjust corners'),
                      style: _outlinedOnDark,
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 6, 16, 0),
              child: FilledButton(
                onPressed: () => Navigator.of(context).pop(_path),
                child: const Text('Use this photo'),
              ),
            ),
            if (_cropped)
              TextButton(
                onPressed: _useFullPhoto,
                child: const Text(
                  'Use the full photo instead',
                  style: TextStyle(color: Colors.white70),
                ),
              )
            else
              const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }
}

final _outlinedOnDark = OutlinedButton.styleFrom(
  foregroundColor: Colors.white,
  side: const BorderSide(color: Colors.white54),
  padding: const EdgeInsets.symmetric(vertical: 14),
);

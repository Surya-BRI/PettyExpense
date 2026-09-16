// THROWAWAY diagnostic screen. Not part of the app. Shows doclens' raw detection
// status and quad coordinates as an on-screen overlay (readable in a phone
// screenshot -- an installed APK has no attached console) -- no capture
// overlay UI, no state machine, no quality gate. Delete this file (and
// lib/probe_main.dart) once the 8:1 aspect ratio / glare validation is done.
import 'dart:async';

import 'package:doclens/doclens.dart';
import 'package:flutter/material.dart';

class DoclensProbeScreen extends StatefulWidget {
  const DoclensProbeScreen({super.key});

  @override
  State<DoclensProbeScreen> createState() => _DoclensProbeScreenState();
}

class _DoclensProbeScreenState extends State<DoclensProbeScreen> {
  late final DoclensController _controller;
  StreamSubscription<DetectionStatus>? _statusSub;
  StreamSubscription<Quad?>? _quadSub;
  int _frame = 0;
  String _statusLine = 'status: starting...';
  String _quadLine = 'quad: -';

  @override
  void initState() {
    super.initState();
    _controller = DoclensController(
      config: const ScannerConfig(
        enableAutoCapture: false,
        enableTelemetryLogging: true,
      ),
    );
    _init();
  }

  Future<void> _init() async {
    await _controller.initialize();
    if (mounted) setState(() {});
    _statusSub = _controller.statusStream.listen((status) {
      final line = 'status: ${status.name}';
      debugPrint('[probe] $line');
      if (mounted) setState(() => _statusLine = line);
    });
    _quadSub = _controller.quadStream.listen((quad) {
      _frame++;
      final line = quad == null
          ? 'quad: frame=$_frame null'
          : 'quad: frame=$_frame area=${quad.area.toStringAsFixed(3)}\n$quad';
      debugPrint('[probe] $line');
      if (mounted) setState(() => _quadLine = line);
    });
  }

  @override
  void dispose() {
    _statusSub?.cancel();
    _quadSub?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_controller.isInitialized) {
      return const Scaffold(
        backgroundColor: Colors.black,
        body: Center(child: CircularProgressIndicator()),
      );
    }
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          DoclensView(controller: _controller),
          Positioned(
            left: 8,
            right: 8,
            top: 40,
            child: _ProbeOverlayText(_statusLine),
          ),
          Positioned(
            left: 8,
            right: 8,
            bottom: 24,
            child: _ProbeOverlayText(_quadLine),
          ),
        ],
      ),
    );
  }
}

/// High-contrast text block (solid dark background, larger font) so status/quad
/// values are legible in a phone screenshot regardless of what's behind them.
class _ProbeOverlayText extends StatelessWidget {
  const _ProbeOverlayText(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: Colors.lightGreenAccent,
          fontSize: 15,
          fontWeight: FontWeight.w600,
          fontFamily: 'monospace',
        ),
      ),
    );
  }
}

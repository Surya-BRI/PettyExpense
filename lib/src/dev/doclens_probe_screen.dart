// THROWAWAY diagnostic screen. Not part of the app. Prints doclens' raw
// detection status and quad coordinates to the console, nothing else -- no
// overlay, no state machine, no quality gate. Delete this file (and
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
  String _lastLine = 'starting...';

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
      // ignore: avoid_print
      print('[probe] status=${status.name}');
    });
    _quadSub = _controller.quadStream.listen((quad) {
      _frame++;
      final line = quad == null
          ? '[probe] frame=$_frame quad=null'
          : '[probe] frame=$_frame area=${quad.area.toStringAsFixed(3)} $quad';
      // ignore: avoid_print
      print(line);
      if (mounted) setState(() => _lastLine = line);
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
            bottom: 24,
            child: Text(
              _lastLine,
              style: const TextStyle(color: Colors.lightGreenAccent, fontSize: 11),
            ),
          ),
        ],
      ),
    );
  }
}

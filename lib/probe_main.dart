// THROWAWAY entry point for the doclens detection probe. Run with:
//   flutter run -t lib/probe_main.dart -d <device-id>
// Does not touch the real app's routing/auth/main.dart at all.
import 'package:flutter/material.dart';

import 'src/dev/doclens_probe_screen.dart';

void main() {
  runApp(const MaterialApp(
    debugShowCheckedModeBanner: false,
    home: DoclensProbeScreen(),
  ));
}

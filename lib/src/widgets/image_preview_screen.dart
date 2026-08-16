import 'package:flutter/material.dart';

/// Full-screen, pinch-to-zoom view of a bill photo — used both for a freshly
/// captured local file (confirm screen) and a fetched receipt image
/// (claim/approval detail), so the viewer itself isn't duplicated per source.
class ImagePreviewScreen extends StatelessWidget {
  const ImagePreviewScreen({super.key, required this.image});

  final Widget image;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Stack(
          children: [
            Positioned.fill(
              child: InteractiveViewer(
                minScale: 1,
                maxScale: 5,
                child: Center(child: image),
              ),
            ),
            Positioned(
              top: 8,
              left: 8,
              child: IconButton(
                onPressed: () => Navigator.of(context).pop(),
                icon: const Icon(Icons.close, color: Colors.white, size: 28),
                style: IconButton.styleFrom(
                  backgroundColor: Colors.black45,
                  shape: const CircleBorder(),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

void openImagePreview(BuildContext context, Widget image) {
  Navigator.of(context).push(
    PageRouteBuilder(
      opaque: false,
      barrierColor: Colors.black,
      pageBuilder: (context, animation, secondaryAnimation) => ImagePreviewScreen(image: image),
    ),
  );
}

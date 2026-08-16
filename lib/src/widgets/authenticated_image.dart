import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../theme/app_theme.dart';
import 'image_preview_screen.dart';

/// Loads a receipt image through [ApiClient.fetchImageBytes] instead of handing
/// a static bearer token to `Image.network` — that path can't recover if the
/// token goes stale mid-session, this one retries once via the shared 401 flow.
/// Shows the app's orange accent border and opens a full-screen zoomable
/// preview on tap, same as the freshly-captured photo on the confirm screen.
class AuthenticatedImage extends ConsumerStatefulWidget {
  const AuthenticatedImage({
    super.key,
    required this.path,
    this.height,
    this.width,
    this.fit = BoxFit.cover,
    this.borderRadius = 12,
  });

  final String path;
  final double? height;
  final double? width;
  final BoxFit fit;
  final double borderRadius;

  @override
  ConsumerState<AuthenticatedImage> createState() => _AuthenticatedImageState();
}

class _AuthenticatedImageState extends ConsumerState<AuthenticatedImage> {
  late Future<Uint8List> _future;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(AuthenticatedImage oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Only re-fetch when the image actually changes — apiClientProvider can
    // rebuild this widget (e.g. after a token refresh) without the path
    // changing at all; re-firing the request every such rebuild is exactly
    // the bug this class exists to avoid (FutureBuilder with an inline
    // `future:` re-invokes the call on every build, restarting the fetch
    // and racing itself — that was the earlier version of this widget).
    if (widget.path != oldWidget.path) {
      _load();
    }
  }

  void _load() {
    _future = ref.read(apiClientProvider).fetchImageBytes(widget.path);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(widget.borderRadius),
        border: Border.all(color: AppColors.orange, width: 2),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(widget.borderRadius - 2),
        child: FutureBuilder<Uint8List>(
          future: _future,
          builder: (context, snapshot) {
            if (snapshot.connectionState != ConnectionState.done) {
              return SizedBox(
                height: widget.height,
                width: widget.width,
                child: const Center(child: CircularProgressIndicator(strokeWidth: 2)),
              );
            }
            if (snapshot.hasError || !snapshot.hasData) {
              return SizedBox(
                height: widget.height ?? 120,
                width: widget.width,
                child: const Center(child: Text('Image unavailable')),
              );
            }
            final bytes = snapshot.data!;
            return GestureDetector(
              onTap: () => openImagePreview(context, Image.memory(bytes)),
              child: Image.memory(
                bytes,
                height: widget.height,
                width: widget.width,
                fit: widget.fit,
              ),
            );
          },
        ),
      ),
    );
  }
}

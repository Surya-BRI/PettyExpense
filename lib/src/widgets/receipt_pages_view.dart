import 'dart:io';

import 'package:flutter/material.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../theme/app_theme.dart';
import 'authenticated_image.dart';
import 'image_preview_screen.dart';

/// Shows every page of a receipt. One page renders exactly as a single image;
/// several pages become a swipeable strip with a "2 / 3" counter and Prev/Next.
class ReceiptPagesView extends StatefulWidget {
  /// Pages just captured on this device (confirm screen before upload).
  const ReceiptPagesView.local(List<String> paths, {super.key, required this.height})
      : _paths = paths,
        _local = true;

  /// Pages stored on the server, fetched with auth via [AuthenticatedImage].
  const ReceiptPagesView.network(List<String> urls, {super.key, required this.height})
      : _paths = urls,
        _local = false;

  final List<String> _paths;
  final bool _local;
  final double height;

  @override
  State<ReceiptPagesView> createState() => _ReceiptPagesViewState();
}

class _ReceiptPagesViewState extends State<ReceiptPagesView> {
  int _page = 0;
  late final PageController _controller = PageController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _goTo(int i) {
    if (i < 0 || i >= widget._paths.length) return;
    _controller.animateToPage(
      i,
      duration: const Duration(milliseconds: 220),
      curve: Curves.easeOut,
    );
  }

  Widget _pageAt(int i) {
    final path = widget._paths[i];
    if (!widget._local) {
      return AuthenticatedImage(path: path, height: widget.height, width: double.infinity);
    }
    return GestureDetector(
      onTap: () => openImagePreview(context, Image.file(File(path))),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.orange, width: 2),
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(14),
          child: Image.file(
            File(path),
            height: widget.height,
            width: double.infinity,
            fit: BoxFit.cover,
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final count = widget._paths.length;
    if (count == 0) return const SizedBox.shrink();
    if (count == 1) return _pageAt(0);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SizedBox(
          height: widget.height + 4, // + the 2px orange border on each side
          child: Stack(
            children: [
              PageView.builder(
                controller: _controller,
                itemCount: count,
                onPageChanged: (i) => setState(() => _page = i),
                itemBuilder: (_, i) => Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 2),
                  child: _pageAt(i),
                ),
              ),
              Positioned(
                top: 10,
                right: 12,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.black.withValues(alpha: 0.6),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${_page + 1} / $count',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 4),
        Align(
          alignment: Alignment.centerRight,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextButton.icon(
                onPressed: _page > 0 ? () => _goTo(_page - 1) : null,
                icon: Icon(PhosphorIcons.caretLeft(), size: 16),
                label: const Text('Prev'),
              ),
              TextButton(
                onPressed: _page < count - 1 ? () => _goTo(_page + 1) : null,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text('Next'),
                    const SizedBox(width: 6),
                    Icon(PhosphorIcons.caretRight(), size: 16),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

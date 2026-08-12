import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../api/api_client.dart';
import '../../theme/app_theme.dart';

/// Simple sheet: camera or gallery only (no tech/OCR wording).
Future<void> showCaptureReceiptSheet(BuildContext context, WidgetRef ref) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (ctx) => const _CaptureReceiptSheet(),
  );
}

class _CaptureReceiptSheet extends ConsumerStatefulWidget {
  const _CaptureReceiptSheet();

  @override
  ConsumerState<_CaptureReceiptSheet> createState() => _CaptureReceiptSheetState();
}

class _CaptureReceiptSheetState extends ConsumerState<_CaptureReceiptSheet> {
  final _picker = ImagePicker();
  bool _busy = false;
  String? _error;

  Future<void> _pick(ImageSource source) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final xfile = await _picker.pickImage(source: source, imageQuality: 85);
      if (xfile == null) {
        setState(() => _busy = false);
        return;
      }
      final draft = await ref.read(apiClientProvider).uploadOcr(File(xfile.path));
      if (!mounted) return;
      Navigator.of(context).pop(); // close sheet
      context.push('/confirm', extra: {
        'ocr': draft,
        'localPath': xfile.path,
      });
    } catch (e) {
      setState(() {
        _busy = false;
        _error = 'Could not upload receipt. Check connection and try again.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: EdgeInsets.fromLTRB(20, 12, 20, 20 + MediaQuery.paddingOf(context).bottom),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.black26,
                borderRadius: BorderRadius.circular(99),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'Add receipt',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
          ),
          const SizedBox(height: 20),
          if (_error != null) ...[
            Text(_error!, style: const TextStyle(color: Colors.red), textAlign: TextAlign.center),
            const SizedBox(height: 12),
          ],
          if (_busy)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 28),
              child: Center(child: CircularProgressIndicator()),
            )
          else ...[
            FilledButton.icon(
              onPressed: () => _pick(ImageSource.camera),
              icon: const Icon(Icons.photo_camera),
              label: const Text('Open camera'),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: () => _pick(ImageSource.gallery),
              icon: const Icon(Icons.photo_library_outlined),
              label: const Text('Upload from gallery'),
            ),
            const SizedBox(height: 4),
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Cancel'),
            ),
          ],
        ],
      ),
    );
  }
}

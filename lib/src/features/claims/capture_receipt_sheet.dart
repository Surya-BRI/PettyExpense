import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../api/api_client.dart';
import '../../theme/app_theme.dart';
import 'bill_line_mode.dart';
import 'guided_capture_screen.dart';

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
  ConsumerState<_CaptureReceiptSheet> createState() =>
      _CaptureReceiptSheetState();
}

class _CaptureReceiptSheetState extends ConsumerState<_CaptureReceiptSheet> {
  final _picker = ImagePicker();
  // Must be chosen before the camera/gallery is enabled.
  BillLineMode? _mode;
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
      await _uploadAndContinue(xfile.path);
    } catch (e) {
      setState(() {
        _busy = false;
        _error = 'Could not upload receipt. Check connection and try again.';
      });
    }
  }

  Future<void> _openGuidedCapture() async {
    final result = await Navigator.of(context, rootNavigator: true)
        .push<GuidedCaptureResult>(
          MaterialPageRoute(builder: (_) => const GuidedCaptureScreen()),
        );
    if (!mounted || result == null) return;
    if (result.useFallback) {
      await _pick(ImageSource.camera);
      return;
    }
    final path = result.imagePath;
    if (path == null) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await _uploadAndContinue(path);
    } catch (e) {
      setState(() {
        _busy = false;
        _error = 'Could not upload receipt. Check connection and try again.';
      });
    }
  }

  Future<void> _uploadAndContinue(String path) async {
    final stored = await ref.read(apiClientProvider).uploadReceipt(File(path));
    if (!mounted) return;
    Navigator.of(context).pop();
    context.push(
      '/confirm',
      extra: {
        'ocr': stored,
        'localPath': path,
        'runOcr': true,
        'lineMode': _mode,
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.zero,
      ),
      padding: EdgeInsets.fromLTRB(
        20,
        14,
        20,
        32 + MediaQuery.paddingOf(context).bottom,
      ),
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
                borderRadius: BorderRadius.zero,
              ),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            'Add receipt',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 28),
          // IntrinsicHeight: both cards share the height of the taller one.
          IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                for (final mode in BillLineMode.values) ...[
                  if (mode != BillLineMode.values.first)
                    const SizedBox(width: 14),
                  Expanded(
                    child: _ModeOption(
                      mode: mode,
                      selected: _mode == mode,
                      enabled: !_busy,
                      onTap: () => setState(() => _mode = mode),
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 30),
          if (_error != null) ...[
            Text(
              _error!,
              style: const TextStyle(color: Colors.red),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
          ],
          if (_busy)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 28),
              child: Column(
                children: [
                  Center(child: CircularProgressIndicator()),
                  SizedBox(height: 12),
                  Text('Saving receipt…', textAlign: TextAlign.center),
                ],
              ),
            )
          else ...[
            if (_mode == null)
              const Padding(
                padding: EdgeInsets.only(bottom: 14),
                child: Text(
                  'Choose the bill type above to continue',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 13,
                  ),
                ),
              ),
            FilledButton.icon(
              onPressed: _mode == null ? null : _openGuidedCapture,
              icon: const Icon(Icons.photo_camera),
              label: const Text('Open camera'),
            ),
            const SizedBox(height: 14),
            OutlinedButton.icon(
              onPressed: _mode == null
                  ? null
                  : () => _pick(ImageSource.gallery),
              icon: const Icon(Icons.photo_library_outlined),
              label: const Text('Upload from gallery'),
            ),
            const SizedBox(height: 10),
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

/// One of the two side-by-side bill-type choices; exactly one can be selected.
class _ModeOption extends StatelessWidget {
  const _ModeOption({
    required this.mode,
    required this.selected,
    required this.enabled,
    required this.onTap,
  });

  final BillLineMode mode;
  final bool selected;
  final bool enabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final accent = selected ? AppColors.orange : AppColors.darkBlue;
    return Semantics(
      button: true,
      selected: selected,
      label: mode.label,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: enabled ? onTap : null,
          borderRadius: BorderRadius.circular(14),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 160),
            padding: const EdgeInsets.fromLTRB(18, 20, 18, 24),
            decoration: BoxDecoration(
              color: selected
                  ? AppColors.orange.withValues(alpha: 0.07)
                  : AppColors.card,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: selected ? AppColors.orange : AppColors.divider,
                width: selected ? 2 : 1,
              ),
              boxShadow: selected
                  ? [
                      BoxShadow(
                        color: AppColors.orange.withValues(alpha: 0.15),
                        blurRadius: 12,
                        offset: const Offset(0, 4),
                      ),
                    ]
                  : null,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 42,
                      height: 42,
                      decoration: BoxDecoration(
                        color: accent.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        mode == BillLineMode.single
                            ? Icons.receipt_long
                            : Icons.format_list_bulleted,
                        color: accent,
                        size: 24,
                      ),
                    ),
                    const Spacer(),
                    AnimatedSwitcher(
                      duration: const Duration(milliseconds: 160),
                      child: selected
                          ? const Icon(
                              Icons.check_circle,
                              key: ValueKey('on'),
                              color: AppColors.orange,
                              size: 22,
                            )
                          : const Icon(
                              Icons.circle_outlined,
                              key: ValueKey('off'),
                              color: AppColors.divider,
                              size: 22,
                            ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                Text(
                  mode.label,
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 15.5,
                    color: selected ? AppColors.orange : AppColors.textPrimary,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

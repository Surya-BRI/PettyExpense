import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../theme/app_theme.dart';
import 'bill_language.dart';
import 'bill_line_mode.dart';
import 'guided_capture_screen.dart';

/// Simple sheet: camera or gallery. Every scan is read by GPT.
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
  BillLanguage _billLanguage = BillLanguage.auto;
  // One page by default; multiple lets the scanner / gallery return several pages.
  bool _multiPage = false;
  bool _busy = false;
  String? _error;

  Future<void> _pick(ImageSource source) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final List<String> paths;
      if (_multiPage && source == ImageSource.gallery) {
        final files = await _picker.pickMultiImage(imageQuality: 85, limit: _maxPages);
        paths = files.map((f) => f.path).toList();
      } else {
        final xfile = await _picker.pickImage(source: source, imageQuality: 85);
        paths = [if (xfile != null) xfile.path];
      }
      if (paths.isEmpty) {
        setState(() => _busy = false);
        return;
      }
      await _uploadAndContinue(paths);
    } catch (e) {
      setState(() {
        _busy = false;
        _error = 'Could not upload receipt. Check connection and try again.';
      });
    }
  }

  /// Camera (Spec 5.1): our capture screen takes a photo only when the user presses the
  /// shutter, then lets them check the crop. (The phone's built-in document scanner was
  /// dropped here: it snaps by itself as soon as it thinks it sees a page, and that can't
  /// be switched off from the app.) Multi-page bills: one shutter press per page, asking
  /// after each whether to add another.
  Future<void> _captureWithCamera() async {
    final pages = <String>[];
    final maxPages = _multiPage ? _maxPages : 1;
    while (pages.length < maxPages) {
      final result = await Navigator.of(context, rootNavigator: true).push<GuidedCaptureResult>(
        MaterialPageRoute(
          builder: (_) => GuidedCaptureScreen(
            pageLabel: _multiPage ? 'Page ${pages.length + 1} of up to $maxPages' : null,
          ),
        ),
      );
      if (!mounted) return;
      if (result == null) break; // closed the camera: keep the pages taken so far
      if (result.useFallback) {
        // Plain system camera -- also shutter-only -- for phones where ours can't run.
        if (pages.isEmpty) await _pick(ImageSource.camera);
        if (pages.isEmpty) return;
        break;
      }
      final path = result.imagePath;
      if (path == null) break;
      pages.add(path);
      if (pages.length >= maxPages || !await _askAddAnotherPage(pages.length)) break;
      if (!mounted) return;
    }
    if (pages.isEmpty || !mounted) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await _uploadAndContinue(pages);
    } catch (e) {
      setState(() {
        _busy = false;
        _error = 'Could not upload receipt. Check connection and try again.';
      });
    }
  }

  Future<bool> _askAddAnotherPage(int taken) async {
    final more = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: Text('Page $taken added'),
        content: const Text('Does this bill have another page?'),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Done')),
          FilledButton(onPressed: () => Navigator.of(ctx).pop(true), child: const Text('Add page')),
        ],
      ),
    );
    return more ?? false;
  }

  /// Uploads every page of the bill in one request, then opens the confirm screen.
  Future<void> _uploadAndContinue(List<String> paths) async {
    final stored = await ref
        .read(apiClientProvider)
        .uploadReceipt([for (final p in paths) File(p)]);
    if (!mounted) return;
    Navigator.of(context).pop();
    context.push(
      '/confirm',
      extra: {
        'ocr': stored,
        'localPaths': paths,
        'runOcr': true,
        'lineMode': _mode,
        'ocrMode': _billLanguage.apiValue,
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
      // Scrolls instead of overflowing on short screens (the toggles + cards + buttons are
      // taller than a small phone's available sheet height).
      child: SingleChildScrollView(
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
          const SizedBox(height: 16),
          _PageCountToggle(
            multiPage: _multiPage,
            enabled: !_busy,
            onChanged: (v) => setState(() => _multiPage = v),
          ),
          const SizedBox(height: 12),
          _BillLanguageToggle(
            value: _billLanguage,
            enabled: !_busy,
            onChanged: (v) => setState(() => _billLanguage = v),
          ),
          const SizedBox(height: 20),
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
              onPressed: _mode == null ? null : _captureWithCamera,
              icon: Icon(PhosphorIcons.camera()),
              label: const Text('Open camera'),
            ),
            const SizedBox(height: 14),
            OutlinedButton.icon(
              onPressed: _mode == null
                  ? null
                  : () => _pick(ImageSource.gallery),
              icon: Icon(PhosphorIcons.image()),
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
      ),
    );
  }
}

const _maxPages = 5;

/// Compact three-way switch: Mixed / English / Arabic, chosen before the camera opens.
class _BillLanguageToggle extends StatelessWidget {
  const _BillLanguageToggle({
    required this.value,
    required this.enabled,
    required this.onChanged,
  });

  final BillLanguage value;
  final bool enabled;
  final ValueChanged<BillLanguage> onChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Bill language',
          style: TextStyle(
            fontWeight: FontWeight.w600,
            color: AppColors.textSecondary,
            fontSize: 13,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.all(3),
          decoration: BoxDecoration(
            color: AppColors.background,
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: AppColors.divider),
          ),
          child: Row(
            children: [
              for (final option in BillLanguage.values)
                Expanded(child: _segment(option)),
            ],
          ),
        ),
      ],
    );
  }

  Widget _segment(BillLanguage option) {
    final selected = value == option;
    final color = selected ? Colors.white : AppColors.textSecondary;
    return Semantics(
      button: true,
      selected: selected,
      label: option.label,
      child: GestureDetector(
        onTap: enabled ? () => onChanged(option) : null,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 160),
          padding: const EdgeInsets.symmetric(vertical: 8),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: selected ? AppColors.orange : Colors.transparent,
            borderRadius: BorderRadius.circular(19),
          ),
          child: Text(
            option.label,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ),
      ),
    );
  }
}

/// Compact two-way switch: is this bill one page or several?
class _PageCountToggle extends StatelessWidget {
  const _PageCountToggle({
    required this.multiPage,
    required this.enabled,
    required this.onChanged,
  });

  final bool multiPage;
  final bool enabled;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        padding: const EdgeInsets.all(3),
        decoration: BoxDecoration(
          color: AppColors.background,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: AppColors.divider),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            _segment('One page', PhosphorIcons.file(), selected: !multiPage, value: false),
            _segment('Multiple pages', PhosphorIcons.files(), selected: multiPage, value: true),
          ],
        ),
      ),
    );
  }

  Widget _segment(String label, IconData icon, {required bool selected, required bool value}) {
    final color = selected ? Colors.white : AppColors.textSecondary;
    return Semantics(
      button: true,
      selected: selected,
      label: label,
      child: GestureDetector(
        onTap: enabled ? () => onChanged(value) : null,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 160),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(
            color: selected ? AppColors.orange : Colors.transparent,
            borderRadius: BorderRadius.circular(19),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 16, color: color),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: color,
                ),
              ),
            ],
          ),
        ),
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
                            ? PhosphorIcons.receipt()
                            : PhosphorIcons.listBullets(),
                        color: accent,
                        size: 24,
                      ),
                    ),
                    const Spacer(),
                    AnimatedSwitcher(
                      duration: const Duration(milliseconds: 160),
                      child: selected
                          ? Icon(
                              PhosphorIcons.checkCircle(PhosphorIconsStyle.fill),
                              key: const ValueKey('on'),
                              color: AppColors.orange,
                              size: 22,
                            )
                          : Icon(
                              PhosphorIcons.circle(),
                              key: const ValueKey('off'),
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

import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/models.dart';
import '../../services/offline_bills/offline_bill_store.dart';
import '../../services/offline_bills/offline_bill_sync.dart';
import '../../theme/app_theme.dart';

/// Opens an uploaded offline bill on the normal Confirm screen: it's read there (as for a
/// fresh scan) and the employee checks and submits it.
void openOfflineBill(BuildContext context, OfflineBill bill) {
  context.push(
    '/confirm',
    extra: {
      'ocr': OcrResult(receiptId: bill.receiptId ?? 0, s3Key: bill.s3Key ?? '', vendor: '', date: ''),
      'localPaths': bill.pagePaths,
      'runOcr': true,
      'lineMode': bill.lineMode,
      'ocrMode': bill.ocrMode,
      'offlineBillId': bill.id,
    },
  );
}

/// My Claims: bills scanned without a connection -- "Waiting to upload" and, once uploaded,
/// "Ready to review". Hidden when there are none.
class OfflineBillsCard extends ConsumerWidget {
  const OfflineBillsCard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bills = ref.watch(offlineBillsProvider);
    if (bills.isEmpty) return const SizedBox.shrink();
    final ready = [for (final b in bills) if (b.isReady) b];
    final waiting = [for (final b in bills) if (!b.isReady) b];
    final error = waiting.map((b) => b.lastError).whereType<String>().firstOrNull;

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.orange.withValues(alpha: 0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (ready.isNotEmpty) ...[
            _Header(
              icon: PhosphorIcons.checkCircle(PhosphorIconsStyle.fill),
              color: AppColors.success,
              title: 'Ready to review (${ready.length})',
              subtitle: 'Uploaded. Tap a bill to check and submit it.',
            ),
            const SizedBox(height: 8),
            _Thumbs(bills: ready, onTap: (b) => openOfflineBill(context, b)),
          ],
          if (ready.isNotEmpty && waiting.isNotEmpty) const Divider(height: 22),
          if (waiting.isNotEmpty) ...[
            _Header(
              icon: PhosphorIcons.cloudSlash(),
              color: AppColors.orange,
              title: 'Waiting to upload (${waiting.length})',
              subtitle: error != null
                  ? "Couldn't upload: $error"
                  : "Saved on this phone. It uploads by itself when you're back online.",
              trailing: TextButton(
                onPressed: () async {
                  final messenger = ScaffoldMessenger.of(context);
                  final n = await ref.read(offlineBillsProvider.notifier).sync();
                  if (n == 0) {
                    messenger.showSnackBar(
                      const SnackBar(content: Text('Still no connection. The bill stays saved on this phone.')),
                    );
                  }
                },
                child: const Text('Retry now'),
              ),
            ),
            const SizedBox(height: 8),
            _Thumbs(bills: waiting),
          ],
        ],
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.icon, required this.color, required this.title, required this.subtitle, this.trailing});

  final IconData icon;
  final Color color;
  final String title;
  final String subtitle;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(padding: const EdgeInsets.only(top: 2), child: Icon(icon, color: color, size: 20)),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14.5)),
              const SizedBox(height: 2),
              Text(subtitle, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12.5, height: 1.3)),
            ],
          ),
        ),
        ?trailing,
      ],
    );
  }
}

/// One thumbnail per bill (first page), with a page count and a discard button.
class _Thumbs extends ConsumerWidget {
  const _Thumbs({required this.bills, this.onTap});

  final List<OfflineBill> bills;
  final void Function(OfflineBill)? onTap;

  Future<void> _discard(BuildContext context, WidgetRef ref, OfflineBill bill) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Discard this bill?'),
        content: const Text('The scanned photo is deleted from this phone. This cannot be undone.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Keep')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Discard')),
        ],
      ),
    );
    if (ok == true) await ref.read(offlineBillsProvider.notifier).remove(bill.id);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SizedBox(
      height: 84,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: bills.length,
        separatorBuilder: (_, _) => const SizedBox(width: 10),
        itemBuilder: (context, i) {
          final bill = bills[i];
          return SizedBox(
            width: 72,
            child: Stack(
              clipBehavior: Clip.none,
              children: [
                Positioned.fill(
                  top: 8,
                  right: 8,
                  child: InkWell(
                    key: Key('offline_bill_${bill.id}'),
                    onTap: onTap == null ? null : () => onTap!(bill),
                    borderRadius: BorderRadius.circular(8),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Container(
                        color: AppColors.background,
                        child: bill.pagePaths.isEmpty
                            ? const SizedBox()
                            : Image.file(
                                File(bill.pagePaths.first),
                                fit: BoxFit.cover,
                                errorBuilder: (_, _, _) =>
                                    Icon(PhosphorIcons.receipt(), color: AppColors.textSecondary),
                              ),
                      ),
                    ),
                  ),
                ),
                if (bill.pagePaths.length > 1)
                  Positioned(
                    left: 4,
                    bottom: 4,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                      color: Colors.black54,
                      child: Text(
                        '${bill.pagePaths.length} pages',
                        style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w600),
                      ),
                    ),
                  ),
                Positioned(
                  top: 0,
                  right: 0,
                  child: GestureDetector(
                    key: Key('discard_offline_bill_${bill.id}'),
                    onTap: () => _discard(context, ref, bill),
                    child: Container(
                      padding: const EdgeInsets.all(3),
                      decoration: const BoxDecoration(color: AppColors.danger, shape: BoxShape.circle),
                      child: const Icon(Icons.close, size: 12, color: Colors.white),
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

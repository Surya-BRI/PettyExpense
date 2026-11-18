import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../theme/app_theme.dart';
import '../../utils/dubai_time.dart';
import '../../utils/money.dart';
import '../../widgets/app_nav_drawer.dart';
import '../../widgets/brand_app_bar.dart';
import 'admin_providers.dart';

/// Company filter for the Aging report (null = all companies).
final agingRegionFilterProvider = StateProvider.autoDispose<int?>((ref) => null);

final agingReportProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) {
  final regionId = ref.watch(agingRegionFilterProvider);
  return ref.watch(apiClientProvider).agingReport(regionId: regionId);
});

/// Admin: every bill waiting on an approver, most overdue first, with its SLA status
/// (on time / breached / escalated) and how long it has waited.
class AgingReportScreen extends ConsumerWidget {
  const AgingReportScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(agingReportProvider);
    return Scaffold(
      backgroundColor: AppColors.background,
      drawer: const AppNavDrawer(),
      appBar: const BrandAppBar(title: 'Aging report'),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(agingReportProvider),
        child: async.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => ListView(
            children: [
              Padding(padding: const EdgeInsets.all(24), child: Text('$e', textAlign: TextAlign.center)),
            ],
          ),
          data: (data) => AgingReportView(data: data),
        ),
      ),
    );
  }
}

/// The report body, separate from the provider so it can be tested with fixed data.
class AgingReportView extends ConsumerWidget {
  const AgingReportView({super.key, required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final summary = Map<String, dynamic>.from(data['summary'] as Map? ?? const {});
    final items = [for (final i in (data['items'] as List? ?? const [])) Map<String, dynamic>.from(i as Map)];
    final bucketLabels = Map<String, dynamic>.from(data['bucket_labels'] as Map? ?? const {});
    final buckets = Map<String, dynamic>.from(summary['buckets'] as Map? ?? const {});
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
      children: [
        const _CompanyFilter(),
        const SizedBox(height: 12),
        Row(
          children: [
            _SummaryTile(label: 'Pending', value: summary['pending'] ?? 0, color: AppColors.darkBlue),
            const SizedBox(width: 8),
            _SummaryTile(label: 'Breached', value: summary['breached'] ?? 0, color: const Color(0xFFB45309)),
            const SizedBox(width: 8),
            _SummaryTile(label: 'Escalated', value: summary['escalated'] ?? 0, color: AppColors.danger),
          ],
        ),
        if (bucketLabels.isNotEmpty) ...[
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: [
              for (final e in bucketLabels.entries)
                Chip(
                  visualDensity: VisualDensity.compact,
                  label: Text('${e.value}: ${buckets[e.key] ?? 0}', style: const TextStyle(fontSize: 12)),
                ),
            ],
          ),
        ],
        const SizedBox(height: 12),
        if (items.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 48),
            child: Text(
              'No bills are waiting for approval',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textSecondary),
            ),
          )
        else
          for (final item in items) ...[
            _AgingCard(item: item),
            const SizedBox(height: 10),
          ],
      ],
    );
  }
}

class _CompanyFilter extends ConsumerWidget {
  const _CompanyFilter();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final regions = ref.watch(adminRegionsProvider).valueOrNull ?? const [];
    final selected = ref.watch(agingRegionFilterProvider);
    if (regions.isEmpty) return const SizedBox.shrink();
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          ChoiceChip(
            label: const Text('All companies'),
            selected: selected == null,
            onSelected: (_) => ref.read(agingRegionFilterProvider.notifier).state = null,
          ),
          for (final r in regions) ...[
            const SizedBox(width: 8),
            ChoiceChip(
              label: Text(companyTitle(r)),
              selected: selected == r.id,
              onSelected: (_) => ref.read(agingRegionFilterProvider.notifier).state = r.id,
            ),
          ],
        ],
      ),
    );
  }
}

class _SummaryTile extends StatelessWidget {
  const _SummaryTile({required this.label, required this.value, required this.color});

  final String label;
  final Object value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.divider),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('$value', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: color)),
            const SizedBox(height: 2),
            Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12.5)),
          ],
        ),
      ),
    );
  }
}

class _AgingCard extends StatelessWidget {
  const _AgingCard({required this.item});

  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context) {
    final status = item['sla_status'] as String? ?? 'on_time';
    final approvers = [for (final a in (item['approvers'] as List? ?? const [])) '$a'];
    final total = (item['total_amount'] as num?) ?? 0;
    final currency = item['currency'] as String? ?? '';
    final overdue = item['overdue_text'] as String?;
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: status == 'on_time' ? AppColors.divider : _statusColor(status).withValues(alpha: 0.5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '#${item['transaction_id']} · ${item['employee_name'] ?? '-'}',
                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14.5),
                ),
              ),
              _StatusBadge(status: status),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            [
              formatMoney(currency, total),
              if ((item['vendor'] as String?)?.isNotEmpty ?? false) item['vendor'],
              if (item['company'] != null) item['company'],
            ].join(' · '),
            style: const TextStyle(color: AppColors.textSecondary, fontSize: 12.5),
          ),
          const SizedBox(height: 10),
          _Line(icon: PhosphorIcons.userCircle(), text: 'With ${item['stage_label']}: ${approvers.isEmpty ? '-' : approvers.join(', ')}'),
          _Line(icon: PhosphorIcons.hourglassMedium(), text: 'Waiting ${item['waiting_text']}'),
          _Line(
            icon: PhosphorIcons.timer(),
            text: overdue == null
                ? 'Due ${formatDubaiTime(item['stage_due_at'] as String?)}'
                : 'Overdue by $overdue (was due ${formatDubaiTime(item['stage_due_at'] as String?)})',
            color: overdue == null ? null : _statusColor(status),
          ),
        ],
      ),
    );
  }
}

Color _statusColor(String status) => switch (status) {
      'escalated' => AppColors.danger,
      'breached' => const Color(0xFFB45309),
      _ => AppColors.success,
    };

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final label = switch (status) {
      'escalated' => 'Escalated',
      'breached' => 'SLA breached',
      _ => 'On time',
    };
    final color = _statusColor(status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(6)),
      child: Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w700, fontSize: 11.5)),
    );
  }
}

class _Line extends StatelessWidget {
  const _Line({required this.icon, required this.text, this.color});

  final IconData icon;
  final String text;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 15, color: color ?? AppColors.textSecondary),
          const SizedBox(width: 6),
          Expanded(child: Text(text, style: TextStyle(fontSize: 13, color: color ?? AppColors.textPrimary))),
        ],
      ),
    );
  }
}

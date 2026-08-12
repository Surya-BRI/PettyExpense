import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../widgets/brand_app_bar.dart';
import '../shared/status_chip.dart';

final approvalsQueueProvider =
    FutureProvider.autoDispose.family<List<ExpenseClaim>, String>((ref, stage) {
  return ref.watch(apiClientProvider).approvalsQueue(stage);
});

const _stageLabels = {
  'hod': 'HOD queue',
  'department_hod': 'Department HOD queue',
  'accountant': 'Accountant queue',
  'finance_manager': 'Finance Manager queue',
};

/// One screen, parameterized by stage — an HOD and an Accountant see the same
/// widget tree, just filtered to their own stage via the backend query.
class ApprovalQueueScreen extends ConsumerWidget {
  const ApprovalQueueScreen({super.key, required this.stage});

  final String stage;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(approvalsQueueProvider(stage));
    final currency = NumberFormat.currency(locale: 'en_IN', symbol: '₹');

    return Scaffold(
      appBar: BrandAppBar(title: _stageLabels[stage] ?? 'Approvals'),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text('$e', textAlign: TextAlign.center),
          ),
        ),
        data: (claims) {
          if (claims.isEmpty) {
            return const Center(child: Text('Nothing waiting for your approval.'));
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: claims.length,
            separatorBuilder: (context, index) => const SizedBox(height: 10),
            itemBuilder: (context, i) {
              final c = claims[i];
              return Material(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(14),
                child: InkWell(
                  borderRadius: BorderRadius.circular(14),
                  onTap: () => context.push('/approvals/$stage/${c.id}'),
                  child: Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppColors.divider),
                    ),
                    padding: const EdgeInsets.all(14),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                c.vendor,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w700,
                                  color: AppColors.textPrimary,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '${currency.format(c.amount)} · ${c.category} · employee #${c.employeeId}',
                                style: const TextStyle(color: AppColors.textSecondary),
                              ),
                            ],
                          ),
                        ),
                        StatusChip(status: c.status),
                      ],
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

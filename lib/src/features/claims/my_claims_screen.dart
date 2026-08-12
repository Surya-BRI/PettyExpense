import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../widgets/brand_app_bar.dart';
import '../shared/status_chip.dart';

final myClaimsProvider = FutureProvider.autoDispose<List<ExpenseClaim>>((ref) {
  return ref.watch(apiClientProvider).myClaims();
});

class MyClaimsScreen extends ConsumerWidget {
  const MyClaimsScreen({super.key});

  Color _statusAccent(String status) {
    switch (status) {
      case 'submitted':
        return AppColors.orange;
      case 'approved':
        return AppColors.success;
      case 'rejected':
        return AppColors.danger;
      case 'disputed':
        return AppColors.orange;
      case 'paid':
        return AppColors.darkBlue;
      default:
        return AppColors.divider;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(myClaimsProvider);
    final currency = NumberFormat.currency(locale: 'en_IN', symbol: '₹');

    return Scaffold(
      appBar: const BrandAppBar(title: 'My claims'),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (claims) {
          if (claims.isEmpty) {
            return const Center(child: Text('No claims yet. Capture a receipt to start.'));
          }
          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
            itemCount: claims.length,
            separatorBuilder: (context, index) => const SizedBox(height: 12),
            itemBuilder: (context, i) {
              final c = claims[i];
              return Material(
                color: AppColors.card,
                elevation: 0,
                borderRadius: BorderRadius.circular(12),
                child: InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: () => context.push('/claim/${c.id}'),
                  child: Ink(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.divider),
                    ),
                    child: IntrinsicHeight(
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Container(
                            width: 3,
                            decoration: BoxDecoration(
                              color: _statusAccent(c.status),
                              borderRadius: const BorderRadius.only(
                                topLeft: Radius.circular(11),
                                bottomLeft: Radius.circular(11),
                              ),
                            ),
                          ),
                          Expanded(
                            child: Padding(
                              padding: const EdgeInsets.fromLTRB(12, 12, 12, 8),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Expanded(
                                        child: Text(
                                          c.vendor,
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                          style: const TextStyle(
                                            fontWeight: FontWeight.w700,
                                            fontSize: 15,
                                            height: 1.25,
                                            color: AppColors.textPrimary,
                                          ),
                                        ),
                                      ),
                                      const SizedBox(width: 8),
                                      StatusChip(status: c.status),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Row(
                                    children: [
                                      Text(
                                        currency.format(c.amount),
                                        style: const TextStyle(
                                          fontSize: 13,
                                          fontWeight: FontWeight.w600,
                                          color: AppColors.textPrimary,
                                        ),
                                      ),
                                      const Padding(
                                        padding: EdgeInsets.symmetric(horizontal: 6),
                                        child: Text(
                                          '·',
                                          style: TextStyle(
                                            color: AppColors.textSecondary,
                                            fontSize: 13,
                                          ),
                                        ),
                                      ),
                                      Text(
                                        c.billDate ?? '-',
                                        style: const TextStyle(
                                          fontSize: 12,
                                          color: AppColors.textSecondary,
                                        ),
                                      ),
                                      const Spacer(),
                                      TextButton(
                                        style: TextButton.styleFrom(
                                          foregroundColor: AppColors.brightBlue,
                                          padding: const EdgeInsets.symmetric(
                                            horizontal: 4,
                                          ),
                                          minimumSize: Size.zero,
                                          tapTargetSize:
                                              MaterialTapTargetSize.shrinkWrap,
                                          visualDensity: VisualDensity.compact,
                                        ),
                                        onPressed: () =>
                                            context.push('/claim/${c.id}'),
                                        child: const Text(
                                          'View claim',
                                          style: TextStyle(
                                            fontSize: 13,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
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

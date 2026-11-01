import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/enums.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/money.dart';
import '../../widgets/app_nav_drawer.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/pca_fund_figures.dart';
import '../authentication/auth_controller.dart';

final myFundsProvider = FutureProvider.autoDispose<List<PettyCashFund>>((ref) {
  return ref.watch(apiClientProvider).myFunds();
});

class MyFundsScreen extends ConsumerWidget {
  const MyFundsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final role = UserRoleX.fromJson(ref.watch(authControllerProvider).user?.role);
    final employeeView = role == UserRole.employee;
    final async = ref.watch(myFundsProvider);
    return Scaffold(
      backgroundColor: AppColors.background,
      drawer: const AppNavDrawer(),
      appBar: const BrandAppBar(title: 'Petty cash', automaticallyImplyLeading: true),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (funds) {
          final depts = [for (final f in funds) if (f.ownerType == 'department') f];
          if (depts.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'No petty cash is set up for your department yet. Ask Admin to set an approved limit.',
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
            itemCount: depts.length,
            separatorBuilder: (_, _) => const SizedBox(height: 10),
            itemBuilder: (context, i) => _DepartmentBalanceCard(fund: depts[i], remainingOnly: employeeView),
          );
        },
      ),
    );
  }
}

class _DepartmentBalanceCard extends StatelessWidget {
  const _DepartmentBalanceCard({required this.fund, required this.remainingOnly});
  final PettyCashFund fund;
  final bool remainingOnly;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              fund.departmentName ?? fund.label ?? 'Department',
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
            ),
            const SizedBox(height: 4),
            Text(
              [fund.regionCode, if (!remainingOnly) 'Department pot'].whereType<String>().join(' · '),
              style: const TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 14),
            if (remainingOnly) ...[
              const Text('Left', style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
              const SizedBox(height: 4),
              Text(
                formatMoney(fund.currency, fund.available),
                style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 28, height: 1.1),
              ),
            ] else ...[
              PcaFundFigures(fund: fund),
              const SizedBox(height: 8),
              const Text(
                'Reimbursement claims do not debit this pot.',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 12),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

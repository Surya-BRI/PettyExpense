import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../widgets/app_nav_drawer.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/region_branding.dart';
import 'admin_providers.dart';

class AdminHubScreen extends ConsumerWidget {
  const AdminHubScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(adminRegionsProvider);
    return Scaffold(
      backgroundColor: AppColors.background,
      drawer: const AppNavDrawer(),
      appBar: BrandAppBar(
        title: 'Companies',
        actions: [
          IconButton(
            tooltip: 'People',
            onPressed: () => context.push('/admin/people'),
            icon: Icon(PhosphorIcons.users()),
          ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text('$e', textAlign: TextAlign.center),
          ),
        ),
        data: (regions) {
          if (regions.isEmpty) {
            return const Center(child: Text('No companies configured'));
          }
          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
            itemCount: regions.length + 1,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, i) {
              if (i == 0) {
                return const Padding(
                  padding: EdgeInsets.only(bottom: 4),
                  child: Text(
                    'Open a company to set department limits, request top-ups, and change the name or logo. '
                    'Professional Signs gives each employee one advance instead: see Advances in the menu.',
                    style: TextStyle(color: AppColors.textSecondary, height: 1.35),
                  ),
                );
              }
              final r = regions[i - 1];
              return _CompanyCard(
                region: r,
                onTap: () => context.push('/admin/companies/${r.id}'),
              );
            },
          );
        },
      ),
    );
  }
}

class _CompanyCard extends StatelessWidget {
  const _CompanyCard({required this.region, required this.onTap});

  final RegionConfig region;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.card,
      elevation: 0,
      borderRadius: BorderRadius.circular(16),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              height: 92,
              color: const Color(0xFFF4F6F8),
              padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 18),
              child: RegionLogo(regionCode: region.regionCode, fit: BoxFit.contain, alignment: Alignment.center),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 12, 16),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          companyTitle(region),
                          style: const TextStyle(
                            fontWeight: FontWeight.w800,
                            fontSize: 16,
                            height: 1.25,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 8,
                          runSpacing: 6,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: AppColors.lightBlue,
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                region.regionCode.toUpperCase(),
                                style: const TextStyle(
                                  color: AppColors.darkBlue,
                                  fontWeight: FontWeight.w700,
                                  fontSize: 11,
                                  letterSpacing: 0.4,
                                ),
                              ),
                            ),
                            Text(
                              region.usesEmployeeAdvances
                                  ? 'Employee advances, spend by project'
                                  : 'Open for departments and limits',
                              style: TextStyle(
                                color: AppColors.textSecondary,
                                fontSize: 13,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  Icon(PhosphorIcons.caretRight(), color: AppColors.textSecondary, size: 18),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

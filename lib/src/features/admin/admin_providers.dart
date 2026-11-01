import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';

const kAdminRegionOrder = ['DUBAI', 'UAE', 'KSA', 'OMAN'];

String companyTitle(RegionConfig region) {
  final name = region.companyName?.trim();
  if (name != null && name.isNotEmpty) return name;
  return region.regionName;
}

String peopleCountLabel(int n) => n == 1 ? '1 person' : '$n people';

String fundCompanyName(PettyCashFund fund) {
  final company = (fund.companyName ?? '').trim();
  if (company.isNotEmpty) return company;
  final code = (fund.regionCode ?? '').trim();
  return code.isEmpty ? 'Company' : code;
}

String fundCompanyLabel(PettyCashFund fund) {
  final dept = (fund.departmentName ?? fund.label ?? 'Department').trim();
  final company = fundCompanyName(fund);
  if (company == 'Company') return dept;
  return '$dept · $company';
}

final adminRegionsProvider = FutureProvider.autoDispose<List<RegionConfig>>((ref) async {
  final regions = await ref.watch(apiClientProvider).listRegions();
  final sorted = [...regions];
  sorted.sort((a, b) {
    final ai = kAdminRegionOrder.indexOf(a.regionCode.toUpperCase());
    final bi = kAdminRegionOrder.indexOf(b.regionCode.toUpperCase());
    return (ai < 0 ? 99 : ai).compareTo(bi < 0 ? 99 : bi);
  });
  return sorted;
});

final adminFundsProvider = FutureProvider.autoDispose<List<PettyCashFund>>((ref) {
  return ref.watch(apiClientProvider).adminFunds();
});

final departmentFundsProvider = FutureProvider.autoDispose.family<List<DepartmentFund>, int>((ref, regionId) {
  return ref.watch(apiClientProvider).adminDepartmentFunds(regionId);
});

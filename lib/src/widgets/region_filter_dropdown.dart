import 'package:flutter/material.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../theme/app_theme.dart';
import 'app_nav_drawer.dart' show companyLabel;

/// Regions to offer in a list's filter: the ones this person covers (home region +
/// Admin-ticked ones) plus every region actually present in the list. The backend always
/// sends at least the home region, so Admin / unrestricted users rely on [present], and
/// bills routed in from outside the user's regions (cross-department) stay filterable.
///
/// [onlyAllowed] (everyone but Admin): offer just the regions this person covers. HOD,
/// Accountant and Finance Manager are per region (region_scope.py on the backend), so their
/// approvals, top-ups and payments only ever come from those.
List<String> regionFilterOptions(List<String> allowed, Iterable<String?> present, {bool onlyAllowed = false}) {
  final codes = {
    for (final c in allowed)
      if (c.trim().isNotEmpty) c.trim().toUpperCase(),
    if (!onlyAllowed || allowed.isEmpty)
      for (final c in present.whereType<String>())
        if (c.trim().isNotEmpty) c.trim().toUpperCase(),
  };
  return codes.toList()..sort();
}

/// True when [code] passes the filter [selected] (null = all regions). A selected region
/// that is no longer offered in [options] counts as "all", so a stale pick never hides work.
bool regionFilterMatches(String? selected, List<String> options, String? code) {
  if (selected == null || !options.contains(selected)) return true;
  return (code ?? '').trim().toUpperCase() == selected;
}

/// Compact "All regions / UAE / KSA ..." dropdown used on lists that mix regions
/// (approval queue, history, top-ups, payments). Hidden by callers when there is only one region.
class RegionFilterDropdown extends StatelessWidget {
  const RegionFilterDropdown({super.key, required this.options, required this.selected, required this.onChanged});

  final List<String> options;
  final String? selected;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 34,
      padding: const EdgeInsets.only(left: 10, right: 4),
      decoration: BoxDecoration(
        color: AppColors.card,
        border: Border.all(color: AppColors.divider),
        borderRadius: BorderRadius.circular(8),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String?>(
          value: options.contains(selected) ? selected : null,
          isDense: true,
          icon: Icon(PhosphorIcons.caretDown(), size: 14, color: AppColors.textSecondary),
          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
          borderRadius: BorderRadius.circular(8),
          items: [
            const DropdownMenuItem<String?>(value: null, child: Text('All regions')),
            for (final code in options) DropdownMenuItem<String?>(value: code, child: Text(companyLabel(code))),
          ],
          onChanged: onChanged,
        ),
      ),
    );
  }
}

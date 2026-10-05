import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/api_client.dart';
import '../../api/enums.dart';
import '../../api/models.dart';
import '../../routing/role_routes.dart';
import '../authentication/auth_controller.dart';

/// Every claim the signed-in user may see: approvers/admin get the whole company
/// (`/api/admin/claims`), an employee gets only their own (`/api/claims/mine`).
/// Shared by the web dashboard and the all-claims table so both read one list.
final visibleClaimsProvider = FutureProvider.autoDispose<List<ExpenseClaim>>((ref) {
  final user = ref.watch(authControllerProvider).user;
  final api = ref.watch(apiClientProvider);
  final approver = UserRoleX.fromJson(user?.role).isApprover;
  return approver ? api.adminClaims() : api.myClaims();
});

/// Company-wide workflow feed -- approvers only. Null means "not available" (employee,
/// or a backend that predates `/api/admin/activity`), so the panel can hide itself
/// instead of showing an error.
final activityFeedProvider = FutureProvider.autoDispose<List<ActivityItem>?>((ref) async {
  final user = ref.watch(authControllerProvider).user;
  if (!UserRoleX.fromJson(user?.role).isApprover) return null;
  try {
    return await ref.watch(apiClientProvider).activity(limit: 40);
  } catch (_) {
    return null;
  }
});

const kStageLabels = {
  'employee': 'Employee',
  'hod': 'HOD',
  'department_hod': 'Department HOD',
  'accountant': 'Accountant',
  'finance_manager': 'Finance Manager',
};

const kStatusLabels = {
  'draft': 'Draft',
  'submitted': 'Submitted',
  'disputed': 'Disputed',
  'approved': 'Approved',
  'rejected': 'Rejected',
  'paid': 'Paid',
};

const kPendingStatuses = {'submitted', 'disputed'};

double claimTotal(ExpenseClaim c) => c.totalAmount ?? (c.amount + c.vatAmount);

DateTime? claimDate(ExpenseClaim c) {
  final raw = c.submittedAt ?? c.createdAt;
  return raw == null ? null : DateTime.tryParse(raw);
}

/// Approvers open the review screen under THEIR OWN stage, so the approve/dispute/reject
/// controls only appear when the claim is actually waiting on them (same rule as the
/// queue screen); employees open their own claim detail.
void openClaim(BuildContext context, ExpenseClaim claim, UserRole role) {
  if (role.isApprover) {
    final stage = switch (role) {
      // An HOD acts on either the 'hod' or the cross-department 'department_hod' stage.
      UserRole.hod => claim.currentStage == 'department_hod' ? 'department_hod' : 'hod',
      // Admin may act on any stage (backend allows it).
      UserRole.admin => claim.currentStage ?? defaultStageFor(role),
      _ => defaultStageFor(role),
    };
    context.push('/approvals/$stage/${claim.id}');
  } else {
    context.push('/claim/${claim.id}');
  }
}

enum DashboardPeriod { days30, days90, thisYear, all }

extension DashboardPeriodX on DashboardPeriod {
  String get label => switch (this) {
        DashboardPeriod.days30 => 'Last 30 days',
        DashboardPeriod.days90 => 'Last 90 days',
        DashboardPeriod.thisYear => 'This year',
        DashboardPeriod.all => 'All time',
      };

  bool includes(DateTime? date, DateTime now) {
    if (this == DashboardPeriod.all) return true;
    if (date == null) return false;
    return switch (this) {
      DashboardPeriod.days30 => date.isAfter(now.subtract(const Duration(days: 30))),
      DashboardPeriod.days90 => date.isAfter(now.subtract(const Duration(days: 90))),
      DashboardPeriod.thisYear => date.year == now.year,
      DashboardPeriod.all => true,
    };
  }
}

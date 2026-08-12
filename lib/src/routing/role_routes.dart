import '../api/enums.dart';

/// Where a role lands after login / when redirected off submitter-only screens.
String homeRouteFor(UserRole role) {
  if (role == UserRole.employee) return '/claims';
  return '/approvals/${defaultStageFor(role)}';
}

/// Which approval stage a role's queue defaults to.
String defaultStageFor(UserRole role) {
  switch (role) {
    case UserRole.hod:
      return 'hod';
    case UserRole.accountant:
      return 'accountant';
    case UserRole.financeManager:
      return 'finance_manager';
    case UserRole.admin:
      return 'hod';
    case UserRole.employee:
      return 'hod';
  }
}

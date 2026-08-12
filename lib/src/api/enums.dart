/// Role vocabulary matches the backend's ErpMasterExpenseRole codes exactly.
/// 'department_hod' is a workflow *stage*, not a role — an 'hod' user acts on
/// either the 'hod' stage or the 'department_hod' stage depending on the transaction.
enum UserRole { employee, hod, accountant, financeManager, admin }

extension UserRoleX on UserRole {
  static UserRole fromJson(String? value) {
    switch (value) {
      case 'hod':
        return UserRole.hod;
      case 'accountant':
        return UserRole.accountant;
      case 'finance_manager':
        return UserRole.financeManager;
      case 'admin':
        return UserRole.admin;
      case 'employee':
      default:
        return UserRole.employee;
    }
  }

  String toJson() {
    switch (this) {
      case UserRole.hod:
        return 'hod';
      case UserRole.accountant:
        return 'accountant';
      case UserRole.financeManager:
        return 'finance_manager';
      case UserRole.admin:
        return 'admin';
      case UserRole.employee:
        return 'employee';
    }
  }

  /// Any role that can act on an approval queue (not the plain submitter).
  bool get isApprover => this != UserRole.employee;
}

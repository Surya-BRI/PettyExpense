import 'package:expense_app/src/api/enums.dart';
import 'package:expense_app/src/api/models.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> _json(String role, String pcaModel) => {
      'id': 1,
      'display_name': 'Priya',
      'role': role,
      'pca_model': pcaModel,
    };

void main() {
  test('an HOD signed in under Blue Rhine Contracting is an employee there', () {
    final user = AuthUser.fromJson(_json('hod', 'site'));
    expect(user.userRole, UserRole.employee);
    expect(user.isApprover, isFalse);
  });

  test('an HOD stays HOD in a department-pot company', () {
    expect(AuthUser.fromJson(_json('hod', 'department')).userRole, UserRole.hod);
  });

  test('BRC Accounts roles are unchanged', () {
    expect(AuthUser.fromJson(_json('accountant', 'site')).userRole, UserRole.accountant);
    expect(AuthUser.fromJson(_json('head_accountant', 'site')).userRole, UserRole.headAccountant);
  });
}

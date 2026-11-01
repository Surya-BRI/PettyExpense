import 'package:expense_app/src/features/claims/claim_field_validation.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('defaultBillRegion', () {
    test('keeps a value already on the form', () {
      expect(
        defaultBillRegion(
          visibleCodes: const ['DUBAI', 'KSA'],
          current: 'KSA',
          homeRegion: 'DUBAI',
        ),
        'KSA',
      );
    });

    test('uses the employee home region when it is in the list', () {
      expect(
        defaultBillRegion(
          visibleCodes: const ['DUBAI', 'KSA', 'OMAN'],
          homeRegion: 'DUBAI',
        ),
        'DUBAI',
      );
    });

    test('uses the only assigned company when home is missing', () {
      expect(
        defaultBillRegion(visibleCodes: const ['DUBAI']),
        'DUBAI',
      );
    });

    test('does not guess when several companies are allowed and none is home', () {
      expect(
        defaultBillRegion(visibleCodes: const ['DUBAI', 'KSA']),
        isNull,
      );
    });

    test('ignores a home region the employee is not allowed to pick', () {
      expect(
        defaultBillRegion(
          visibleCodes: const ['KSA'],
          homeRegion: 'DUBAI',
        ),
        'KSA',
      );
    });
  });
}

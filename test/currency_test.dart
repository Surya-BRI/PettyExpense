import 'package:expense_app/src/api/models.dart';
import 'package:expense_app/src/utils/currency.dart';
import 'package:expense_app/src/widgets/claim_ui_helpers.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('caption shows the scan-date rate', () {
    expect(
      exchangeRateCaption(
        billCurrency: 'OMR',
        regionCode: 'UAE',
        rate: 9.5412,
        asOf: '2026-10-28',
      ),
      '1 OMR = 9.5412 AED (scan date 2026-10-28)',
    );
  });

  test('same currency as the region has no caption', () {
    expect(
      exchangeRateCaption(billCurrency: 'AED', regionCode: 'UAE', rate: 1),
      isNull,
    );
  });

  test('foreign bill converts to the region amount', () {
    expect(needsRegionConversion('OMR', 'UAE'), isTrue);
    expect(toRegionAmount(20, 9.54), closeTo(190.8, 0.0001));
    expect(needsRegionConversion('AED', 'UAE'), isFalse);
    expect(showsRegionConversion('USD', 'UAE', 3.67), isTrue);
    expect(showsRegionConversion('AED', 'UAE', 1), isFalse);
    expect(showsRegionConversion('USD', 'UAE', 0), isFalse);
  });

  test('detail conversion rows show bill, region total, and rate', () {
    const claim = ExpenseClaim(
      id: 1,
      employeeId: 1,
      amount: 39.99,
      currency: 'USD',
      exchangeRate: 3.67,
      categoryId: 1,
      status: 'submitted',
      regionCode: 'UAE',
      totalAmount: 39.99,
    );
    expect(
      claimConversionDetailRows(claim, 39.99).map((r) => r.label).toList(),
      ['Bill total', 'Region total (AED)'],
    );
    final withRate = claimConversionDetailRows(claim, 39.99, showRate: true);
    expect(withRate.map((r) => r.label).toList(), [
      'Bill total',
      'Region total (AED)',
      'Exchange rate',
    ]);
    expect(withRate[2].value, '1 USD = 3.67 AED');
  });
}

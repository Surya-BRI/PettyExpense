/// Currencies an employee can pick for the bill (what's printed on the receipt).
const kBillCurrencies = <String>[
  'AED',
  'SAR',
  'OMR',
  'QAR',
  'KWD',
  'BHD',
  'USD',
  'EUR',
  'GBP',
  'INR',
];

final Map<String, String> _serverBaseCurrency = {};

/// Records the base currency Admin set for a company (from `/api/regions`).
void rememberRegionBaseCurrency(String regionCode, String? baseCurrency) {
  final base = normalizeBillCurrency(baseCurrency);
  if (regionCode.trim().isEmpty || base == null) return;
  _serverBaseCurrency[regionCode.trim().toUpperCase()] = base;
}

/// Region's books currency — exchange_rate is "1 bill unit = this many base units".
String baseCurrencyForRegion(String? regionCode) {
  final known = _serverBaseCurrency[(regionCode ?? '').trim().toUpperCase()];
  if (known != null) return known;
  switch ((regionCode ?? '').toUpperCase()) {
    case 'DUBAI':
    case 'UAE':
      return 'AED';
    case 'KSA':
      return 'SAR';
    case 'OMAN':
      return 'OMR';
    case 'IN':
      return 'INR';
    default:
      return 'AED';
  }
}

String? normalizeBillCurrency(String? value) {
  if (value == null) return null;
  final c = value.trim().toUpperCase();
  if (!RegExp(r'^[A-Z]{3}$').hasMatch(c)) return null;
  return c;
}

String formatExchangeRate(double rate) {
  if (rate == rate.roundToDouble()) return rate.toStringAsFixed(0);
  var shown = rate.toStringAsFixed(6);
  shown = shown.replaceFirst(RegExp(r'0+$'), '');
  return shown.replaceFirst(RegExp(r'\.$'), '');
}

bool needsRegionConversion(String billCurrency, String? regionCode) {
  final bill = billCurrency.trim().toUpperCase();
  return bill.isNotEmpty && bill != baseCurrencyForRegion(regionCode);
}

/// Foreign bill with a stamped rate — show bill + region amounts on every detail screen.
bool showsRegionConversion(String billCurrency, String? regionCode, double rate) =>
    needsRegionConversion(billCurrency, regionCode) && rate > 0;

double toRegionAmount(double billAmount, double exchangeRate) =>
    billAmount * exchangeRate;

String? exchangeRateCaption({
  required String billCurrency,
  required String? regionCode,
  required double rate,
  String? asOf,
}) {
  final base = baseCurrencyForRegion(regionCode);
  if (billCurrency.isEmpty || billCurrency == base) return null;
  final line = '1 $billCurrency = ${formatExchangeRate(rate)} $base';
  final day = (asOf ?? '').trim();
  if (day.isEmpty) return line;
  return '$line (scan date $day)';
}

List<String> billCurrencyChoices(String? selected) {
  final extra = normalizeBillCurrency(selected);
  if (extra != null && !kBillCurrencies.contains(extra)) {
    return [...kBillCurrencies, extra];
  }
  return kBillCurrencies;
}

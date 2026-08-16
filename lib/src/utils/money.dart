import 'package:intl/intl.dart';

/// All claims carry an explicit currency (AED/SAR) chosen at capture time —
/// there is no locale-specific symbol to special-case, so every currency
/// formats the same way: the code as a prefix plus grouped digits.
String formatMoney(String currency, num amount) {
  return NumberFormat.currency(symbol: '$currency ', decimalDigits: 2).format(amount);
}

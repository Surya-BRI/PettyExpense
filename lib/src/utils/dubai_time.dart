import 'package:intl/intl.dart';

/// Backend timestamps are naive UTC (Python's `datetime.utcnow().isoformat()` -- no 'Z'/offset
/// suffix). Dart's DateTime.parse would otherwise read that string as local time verbatim, which
/// is wrong on any device not already in UTC. This reinterprets the same field values as UTC,
/// then shifts by a fixed +4 hours -- Dubai/UAE has no daylight saving, so this is always exact.
String formatDubaiTime(String? isoUtcNaive) {
  if (isoUtcNaive == null || isoUtcNaive.isEmpty) return '';
  final parsed = DateTime.tryParse(isoUtcNaive);
  if (parsed == null) return '';
  final utc = DateTime.utc(parsed.year, parsed.month, parsed.day, parsed.hour, parsed.minute, parsed.second);
  final dubai = utc.add(const Duration(hours: 4));
  return DateFormat('d MMM yyyy, h:mm a').format(dubai);
}

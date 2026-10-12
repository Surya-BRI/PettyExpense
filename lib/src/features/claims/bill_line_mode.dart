/// What kind of bill the employee is about to scan, chosen on the Add receipt sheet
/// before the camera or gallery opens.
enum BillLineMode {
  /// One amount for the whole bill (fuel, taxi, parking).
  single,

  /// Several line items on one bill (pharmacy, supermarket, hardware store).
  multiple,
}

extension BillLineModeX on BillLineMode {
  String get label => switch (this) {
    BillLineMode.single => 'Single item',
    BillLineMode.multiple => 'Multiple items',
  };

  String get example => switch (this) {
    BillLineMode.single => 'One total for the bill, e.g. fuel or taxi',
    BillLineMode.multiple => 'Several items listed, e.g. pharmacy or supermarket',
  };
}

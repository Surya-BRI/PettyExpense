/// Shared draft-vs-submit field rules used by every path that saves or submits a claim
/// (new capture, editing a saved draft) -- a single source of truth so the rules can't drift
/// between the two.
class ClaimFieldError implements Exception {
  ClaimFieldError(this.message);
  final String message;
  @override
  String toString() => message;
}

/// Throws [ClaimFieldError] on the first violated rule; returns normally on success.
/// `amount`/`categoryId` are required even for a draft -- the backend can't persist a claim
/// without them. Everything else only matters for a real submit: a draft is, by definition,
/// allowed to stay incomplete until the employee comes back to finish it.
void validateClaimFields({
  required bool asDraft,
  required double? amount,
  required int? categoryId,
  required double? vat,
  required double? total,
  required String? currency,
  required String vendorText,
  required String billDateText,
  required String billNumberText,
  String? regionCode,
}) {
  if (amount == null) throw ClaimFieldError('Enter a valid amount');
  if (categoryId == null) throw ClaimFieldError('Select a category / expense type');
  if (vat == null) throw ClaimFieldError('Enter a valid VAT amount');
  if (!asDraft && total == null) throw ClaimFieldError('Enter a valid total amount');
  if (!asDraft && currency == null) throw ClaimFieldError('Select the bill currency');
  if (!asDraft && (regionCode == null || regionCode.trim().isEmpty)) {
    throw ClaimFieldError('Select the region for this bill');
  }
  if (!asDraft && vendorText.trim().isEmpty) throw ClaimFieldError('Enter the vendor name');
  if (!asDraft && billDateText.trim().isEmpty) throw ClaimFieldError('Enter the bill date');
  if (!asDraft && billNumberText.trim().isEmpty) {
    throw ClaimFieldError('Enter the bill / invoice number');
  }
}

/// Region to pre-select on Confirm claim.
///
/// A saved/current value always wins. Otherwise use the employee's login (home)
/// region when it's in the list they can pick from, or the only option when
/// they are assigned to a single company. Multi-region users with no current
/// value still have to pick if their home region isn't in the list.
String? defaultBillRegion({
  required List<String> visibleCodes,
  String? current,
  String? homeRegion,
}) {
  final selected = current?.trim();
  if (selected != null && selected.isNotEmpty) return selected;
  final home = homeRegion?.trim();
  if (home != null && home.isNotEmpty && visibleCodes.contains(home)) {
    return home;
  }
  if (visibleCodes.length == 1) return visibleCodes.first;
  return null;
}

/// Field labels still missing for a real submit -- drives the "still needed to submit" banner
/// shown while a draft is incomplete. Recomputed live, not just after a save.
List<String> missingForSubmit({
  required double? total,
  required String? currency,
  required String vendorText,
  required String billDateText,
  required String billNumberText,
  String? regionCode,
}) {
  final missing = <String>[];
  if (vendorText.trim().isEmpty) missing.add('Vendor');
  if (currency == null) missing.add('Bill currency');
  if (regionCode == null || regionCode.trim().isEmpty) missing.add('Region');
  if (billDateText.trim().isEmpty) missing.add('Bill date');
  if (billNumberText.trim().isEmpty) missing.add('Bill number');
  if (total == null) missing.add('Total amount');
  return missing;
}

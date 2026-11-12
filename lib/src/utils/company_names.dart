/// Company names as ERP knows them. The app's internal company codes (DUBAI, UAE, KSA, OMAN)
/// stay as they are in data and sign-in; everything users see uses ERP's company code and name.
///
/// ERP subsidiary -> app code (backend auth/security.py ERP_SUBSIDIARY_TO_REGION_CODE):
///   BRI UAE                    -> DUBAI  Blue Rhine Industries
///   BRC                        -> UAE    Blue Rhine Contracting
///   BRI PS Saudi, Prosigns KSA -> KSA    Professional Signs (two ERP companies: name only)
///   Prosigns Oman              -> OMAN   Prosigns Oman
library;

/// (ERP company code, company name). A null code shows the name alone.
const Map<String, (String?, String)> kErpCompanies = {
  'DUBAI': ('BRI UAE', 'Blue Rhine Industries'),
  'UAE': ('BRC', 'Blue Rhine Contracting'),
  'KSA': (null, 'Professional Signs'),
  'OMAN': ('Prosigns Oman', 'Prosigns Oman'),
};

/// "BRC · Blue Rhine Contracting", "Professional Signs"; the code itself for an unknown company.
String erpCompanyLabel(String? appCode) {
  final code = (appCode ?? '').trim().toUpperCase();
  final entry = kErpCompanies[code];
  if (entry == null) return code;
  final (erpCode, name) = entry;
  if (erpCode == null || erpCode == name) return name;
  return '$erpCode · $name';
}

/// Short form for chips and tight spaces: ERP's code ("BRI UAE", "BRC"), else the name.
String erpCompanyShort(String? appCode) {
  final code = (appCode ?? '').trim().toUpperCase();
  final entry = kErpCompanies[code];
  if (entry == null) return code;
  return entry.$1 ?? entry.$2;
}

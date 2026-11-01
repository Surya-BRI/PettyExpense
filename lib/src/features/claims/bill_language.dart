/// Language hint for reading the bill. Chosen on Add receipt before the camera opens.
enum BillLanguage {
  auto,
  en,
  ar,
}

extension BillLanguageX on BillLanguage {
  String get apiValue => name;

  String get label => switch (this) {
    BillLanguage.auto => 'Mixed',
    BillLanguage.en => 'English',
    BillLanguage.ar => 'Arabic',
  };

  static BillLanguage fromApi(String? value) {
    return switch ((value ?? 'auto').toLowerCase()) {
      'en' => BillLanguage.en,
      'ar' => BillLanguage.ar,
      _ => BillLanguage.auto,
    };
  }
}

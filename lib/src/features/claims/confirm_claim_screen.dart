import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/currency.dart';
import '../../utils/money.dart';
import '../../widgets/app_nav_drawer.dart' show companyLabel;
import '../../widgets/brand_app_bar.dart';
import '../../widgets/op_code_field.dart';
import '../../widgets/receipt_pages_view.dart';
import '../authentication/auth_controller.dart';
import 'bill_line_mode.dart';
import 'claim_field_validation.dart';
import 'line_items_editor.dart';

final _arabic = RegExp(r'[\u0600-\u06FF]');
final _latin = RegExp(r'[A-Za-z]');

/// Set by ConfirmClaimScreen while it's mounted, so any navigation trigger outside its own
/// widget tree (a bottom-nav tab tap in MainShell, which replaces the route directly instead
/// of going through a Navigator pop) can ask it to confirm before leaving -- otherwise an
/// accidental tap silently discards an OCR'd claim the employee never got to save.
/// Returns true if the caller may go ahead with the navigation it wanted (including after a
/// successful "Save as draft" -- the claim is saved in the background, not shown); false if the
/// user chose to keep editing, or if the save failed and the error needs to stay visible.
final confirmClaimLeaveGuardProvider = StateProvider<Future<bool> Function()?>((ref) => null);

/// Every navigation trigger that can fire while ConfirmClaimScreen is open -- bottom-nav tabs,
/// the drawer, the notification bell, any app-bar nav action -- must route through this instead
/// of calling `context.go`/`context.push` directly, or it silently discards an unsaved,
/// OCR'd-from-the-bill claim with no warning at all.
void navigateGuarded(WidgetRef ref, void Function() navigate) {
  final guard = ref.read(confirmClaimLeaveGuardProvider);
  if (guard == null) {
    navigate();
    return;
  }
  guard().then((shouldProceed) {
    if (shouldProceed) navigate();
  });
}

enum _LeaveAction { cancel, discard, saveDraft }

/// True only when Arabic characters outnumber Latin ones, so mixed
/// OCR reads (e.g. an English name followed by its Arabic translation)
/// don't flip the whole field RTL over a single Arabic word.
bool _isArabicDominant(String text) {
  final arabicCount = _arabic.allMatches(text).length;
  if (arabicCount == 0) return false;
  final latinCount = _latin.allMatches(text).length;
  return arabicCount > latinCount;
}

const _maxOcrAttempts = 1;

// keyboardType only hints the on-screen keyboard, so this is the actual enforcement: at most one decimal point, digits only otherwise.
final _decimalInputFormatters = <TextInputFormatter>[
  FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d{0,2}')),
];

class ConfirmClaimScreen extends ConsumerStatefulWidget {
  const ConfirmClaimScreen({
    super.key,
    this.ocr,
    this.localPaths = const [],
    this.runOcr = false,
    this.lineMode = BillLineMode.single,
    this.ocrMode = 'auto',
    this.existingClaimId,
  }) : assert(
         ocr != null || existingClaimId != null,
         'Provide either a freshly-OCRd ocr result or an existingClaimId to edit',
       );

  final OcrResult? ocr;
  /// Pages just captured on this device, in order (one for a single-page bill).
  final List<String> localPaths;
  final bool runOcr;

  /// Chosen on the Add receipt sheet before scanning.
  final BillLineMode lineMode;

  /// Language hint chosen on Add receipt (`auto` / `en` / `ar`).
  final String ocrMode;

  /// Set instead of [ocr] when opening this screen to edit a previously-saved draft --
  /// fetches and seeds the form from the server instead of from a fresh OCR read, and
  /// "Save"/"Submit" update that existing claim instead of creating a new one.
  final int? existingClaimId;

  @override
  ConsumerState<ConfirmClaimScreen> createState() => _ConfirmClaimScreenState();
}

class _ConfirmClaimScreenState extends ConsumerState<ConfirmClaimScreen> {
  late OcrResult _ocr;
  late final TextEditingController _vendor;
  late final TextEditingController _billNumber;
  late final TextEditingController _amount;
  late final TextEditingController _vat;
  late final TextEditingController _total;
  late final TextEditingController _date;
  late final TextEditingController _remarks;
  int? _categoryId;
  String _type = 'reimbursement';
  List<PettyCashFund> _myFunds = const [];
  String? _currency;
  String? _billRegion;
  List<RegionConfig> _regions = const [];
  // Preview of today's rate from the bill currency into the company's base currency. The
  // server re-quotes and locks the rate at submit; this is display-only.
  ExchangeRateQuote? _quote;
  String? _quoteKey;
  bool _quoteFailed = false;
  bool _busy = false;
  // null when idle; true/false says which of Submit/Save-as-draft is the one in flight, so
  // only that button's label changes -- see _submit().
  bool? _busyAsDraft;
  String? _error;
  // Guards against a second leave-attempt (another nav tap, or the system back button) firing
  // while the "Leave without saving?" dialog from a first attempt is still up -- without this, a
  // quick double-tap across two different exits could open the dialog twice.
  bool _leaveAttemptInProgress = false;
  List<CategoryRef> _categories = const [];

  // Claim-level OP; also the default new line items start from (see onAdd below).
  OpportunityResult? _selectedOp;

  // "Multiple items" bills: one editable draft per item line.
  final List<LineItemDraft> _lines = [];
  bool _showLineProblems = false;
  // True once the user has manually typed in the Amount excl. VAT field in multi mode;
  // while false the field stays in sync with linesTotal - vat automatically.
  bool _amountOverridden = false;
  // When editing an existing claim there's no pre-chosen BillLineMode -- single vs multi is
  // whatever the claim itself already is, set once it loads (see _loadExistingClaim).
  bool _editingMulti = false;
  bool _editingDisputed = false;
  bool get _multi => widget.existingClaimId != null
      ? _editingMulti
      : widget.lineMode == BillLineMode.multiple;

  void _onMoneyFieldsChanged() {
    if (!mounted || _type != 'petty_cash') return;
    setState(() {});
  }

  /// The bill's company gives each employee one advance (Professional Signs): no department
  /// pots, every bill names its project OP code, and lines aren't split by department.
  bool get _employeeAdvances {
    final code = (_billRegion ?? '').toUpperCase();
    if (code.isEmpty) return false;
    for (final r in _regions) {
      if (r.regionCode.toUpperCase() == code) return r.usesEmployeeAdvances;
    }
    final user = ref.read(authControllerProvider).user;
    return (user?.regionCode ?? '').toUpperCase() == code && (user?.usesEmployeeAdvances ?? false);
  }

  /// The bill's company gives each employee one petty cash for all their sites (Blue Rhine
  /// Contracting): no HODs or department pots, every bill names its site's OP code, and a
  /// petty-cash bill comes off the employee's petty cash.
  bool get _sitePots {
    final code = (_billRegion ?? '').toUpperCase();
    if (code.isEmpty) return false;
    for (final r in _regions) {
      if (r.regionCode.toUpperCase() == code) return r.usesSitePots;
    }
    final user = ref.read(authControllerProvider).user;
    return (user?.regionCode ?? '').toUpperCase() == code && (user?.usesSitePots ?? false);
  }

  /// Companies where every bill names its project OP code.
  bool get _needsOpCode => _employeeAdvances || _sitePots;

  static String? _normOp(String? op) {
    final v = (op ?? '').trim().toUpperCase();
    return v.isEmpty ? null : v;
  }

  /// Employee-advance company: every bill names its project -- the claim's OP code, or one
  /// on each item (the server checks the same on submit).
  bool get _missingProject {
    if (!_needsOpCode) return false;
    if (_normOp(_selectedOp?.opCode) != null) return false;
    if (!_multi || _lines.isEmpty) return true;
    return _lines.any((line) => _normOp(line.opResult?.opCode) == null);
  }

  PettyCashFund? get _potForBill {
    final code = _billRegion;
    if (code == null || code.isEmpty) return null;
    if (_employeeAdvances || _sitePots) {
      // One advance per employee, for all their projects.
      for (final fund in _myFunds) {
        if (fund.regionCode == code && fund.ownerType == 'employee') return fund;
      }
      return null;
    }
    PettyCashFund? employee;
    PettyCashFund? department;
    for (final fund in _myFunds) {
      if (fund.regionCode != code) continue;
      if (fund.ownerType == 'employee') employee = fund;
      if (fund.ownerType == 'department') department = fund;
    }
    return employee ?? department;
  }

  double get _claimAmount {
    if (_multi) {
      return double.tryParse(_linesTotal.toStringAsFixed(2)) ?? 0;
    }
    return double.tryParse(_total.text.trim()) ??
        double.tryParse(_amount.text.trim()) ??
        0;
  }

  /// What this bill may use: available minus bills already awaiting approval. A disputed
  /// claim is itself one of those pending bills, so it gets the plain available figure.
  double _usableFor(PettyCashFund pot) =>
      _editingDisputed ? pot.available : pot.uncommitted;

  /// Parts of this bill owned by another department (department name → amount on the
  /// bill), e.g. IT items on a Sales bill. Those go to that department's HOD and, for
  /// petty cash, come out of that department's fund — the server checks those funds.
  Map<String, double> get _otherDepartmentAmounts {
    // Employee-advance company: the employee's own HOD approves the whole bill. Site-pot
    // company: no HODs, the bill comes off the employee's site pot.
    if (_employeeAdvances || _sitePots) return const {};
    final own = ref.read(authControllerProvider).user?.departmentId;
    String? otherFor(int? categoryId) {
      for (final c in _categories) {
        if (c.id == categoryId) return c.otherDepartmentFor(own);
      }
      return null;
    }

    final out = <String, double>{};
    if (!_multi) {
      final dept = otherFor(_categoryId);
      if (dept != null) out[dept] = _claimAmount;
      return out;
    }
    for (final line in _lines) {
      final dept = otherFor(line.categoryId ?? _categoryId);
      if (dept == null) continue;
      out[dept] = (out[dept] ?? 0) + (line.amountValue ?? 0);
    }
    return out;
  }

  /// The part of the bill paid from the employee's own pot.
  double get _ownPotAmount {
    final others = _otherDepartmentAmounts.values.fold(0.0, (sum, v) => sum + v);
    return (_claimAmount - others).clamp(0.0, double.infinity);
  }

  String? get _otherDepartmentNote {
    final others = _otherDepartmentAmounts;
    if (others.isEmpty) return null;
    final parts = [
      for (final e in others.entries) '${e.key} items (${formatMoney(_currency ?? '', e.value)})',
    ];
    final depts = others.keys.join(' / ');
    return _type == 'petty_cash'
        ? '${parts.join(', ')} come out of $depts petty cash and need $depts HOD approval.'
        : '${parts.join(', ')} need $depts HOD approval.';
  }

  /// 1 bill unit in the company's base currency; null while the rate is unknown.
  double? get _rateToBase {
    final bill = (_currency ?? '').toUpperCase();
    if (bill.isEmpty || bill == _baseCurrency) return 1.0;
    final q = _quote;
    return q != null && q.billCurrency == bill && q.baseCurrency == _baseCurrency ? q.rate : null;
  }

  void _scheduleQuote() => WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _refreshQuote();
      });

  Future<void> _refreshQuote() async {
    final bill = (_currency ?? '').toUpperCase();
    final region = _billRegion ?? '';
    final key = '$bill>$region';
    if (key == _quoteKey) return;
    _quoteKey = key;
    if (bill.isEmpty || region.isEmpty || bill == _baseCurrency) {
      if (mounted) setState(() => _quoteFailed = false);
      return;
    }
    try {
      final q = await ref.read(apiClientProvider).lookupExchangeRate(from: bill, regionCode: region);
      if (!mounted || _quoteKey != key) return;
      rememberRegionBaseCurrency(region, q.baseCurrency);
      setState(() {
        _quote = q;
        _quoteFailed = false;
      });
    } catch (_) {
      if (mounted && _quoteKey == key) setState(() => _quoteFailed = true);
    }
  }

  bool get _pettyCashBlocksSubmit {
    if (_type != 'petty_cash') return false;
    final ownPart = _ownPotAmount;
    if (ownPart <= 0.004) return false;
    final pot = _potForBill;
    if (pot == null) return true;
    if ((_employeeAdvances || _sitePots) && pot.approvedLimit <= 0) return true; // not set yet
    // The fund is held in the company's base currency; with no rate yet the server decides.
    final rate = pot.currency.toUpperCase() == (_currency ?? '').toUpperCase() ? 1.0 : _rateToBase;
    if (rate == null) return false;
    return ownPart * rate > _usableFor(pot) + 0.004;
  }

  String get _pettyCashBlockMessage {
    if (_billRegion == null || _billRegion!.isEmpty) {
      return 'Select the company for this bill before submitting petty cash. '
          'You can still save as draft.';
    }
    final pot = _potForBill;
    if (_sitePots) {
      if (pot == null || pot.approvedLimit <= 0) {
        return 'You don\'t have petty cash in this company. Ask the Accountant to set it, '
            'or file this bill as a reimbursement.';
      }
      final left = formatMoney(pot.currency, _usableFor(pot) < 0 ? 0 : _usableFor(pot));
      return 'This bill is more than what\'s left of your petty cash ($left left). '
          'File the extra as a reimbursement, or wait for a top-up.';
    }
    if (_employeeAdvances) {
      if (pot == null || pot.approvedLimit <= 0) {
        return 'You don\'t have a petty cash advance in this company. '
            'File this bill as a reimbursement instead.';
      }
      final rate = pot.currency.toUpperCase() == (_currency ?? '').toUpperCase() ? 1.0 : _rateToBase;
      final converted = rate != null && rate != 1.0 ? ' (${formatMoney(pot.currency, _ownPotAmount * rate)})' : '';
      final left = formatMoney(pot.currency, _usableFor(pot) < 0 ? 0 : _usableFor(pot));
      if (pot.spendLimit != null) {
        // Hard limit (50% of the PCA) until the approved bills are paid (which refills it).
        return 'This bill$converted is more than you can use now: only '
            '${formatMoney(pot.currency, pot.spendLimit!)} of your petty cash can be used until your '
            'approved bills are paid ($left left). Wait for Accounts to pay them, or file this as a '
            'reimbursement.';
      }
      return 'This bill$converted is more than what\'s left of your petty cash advance '
          '($left left). File the extra as a reimbursement, or wait for a top-up.';
    }
    if (pot == null) {
      return 'No petty cash limit is set for this department in this company. '
          'You can still save as draft.';
    }
    final left = formatMoney(pot.currency, _usableFor(pot));
    final subject = _otherDepartmentAmounts.isEmpty ? 'This bill' : 'Your department\'s part of this bill';
    final rate = _rateToBase;
    final converted = rate != null && pot.currency.toUpperCase() != (_currency ?? '').toUpperCase()
        ? ' (${formatMoney(pot.currency, _ownPotAmount * rate)})'
        : '';
    return '$subject$converted exceeds available petty cash ($left left). '
        'Submit a smaller amount or wait for a top-up. You can still save as draft.';
  }

  bool _analyzing = false;
  bool _ocrFailed = false;
  // Set once an existing draft loads -- the server-hosted receipt image to show instead of a
  // freshly-captured local file (there isn't one when editing, only when capturing).
  List<String> _existingReceiptPages = const [];
  // Invoice-already-submitted warning from a loaded draft (OCR's copy lives on `_ocr`).
  DuplicateWarning? _loadedDuplicateWarning;
  // The invoice number that clashed -- submit is blocked only while the field still matches this.
  String? _blockedInvoice;
  int _progress = 0;
  Timer? _ticker;

  @override
  void initState() {
    super.initState();
    _vendor = TextEditingController();
    _billNumber = TextEditingController();
    _amount = TextEditingController();
    _vat = TextEditingController();
    _total = TextEditingController();
    _date = TextEditingController();
    _remarks = TextEditingController();
    _amount.addListener(_onMoneyFieldsChanged);
    _vat.addListener(_onMoneyFieldsChanged);
    _total.addListener(_onMoneyFieldsChanged);
    _loadReferenceData();
    if (widget.existingClaimId != null) {
      // No fresh OCR data to seed from when editing a saved draft -- an inert placeholder so
      // every other `_ocr.` reference in this file (confidence badges, the duplicate/
      // reconciliation banners, the OCR-retry path) reads as "nothing to show" rather than
      // needing its own edit-mode branch everywhere it's used.
      _ocr = const OcrResult(receiptId: 0, s3Key: '', vendor: '', date: '');
      _analyzing = true;
      WidgetsBinding.instance.addPostFrameCallback((_) => _loadExistingClaim());
    } else {
      _ocr = widget.ocr!;
      _vendor.text = _ocr.vendor.trim();
      _billNumber.text = _ocr.billNumber ?? '';
      _amount.text = _money(_ocr.amount);
      _vat.text = _money(_ocr.vatAmount);
      _total.text = _money(_ocr.totalAmount);
      _date.text = _ocr.date;
      _currency = _normalizeCurrency(_ocr.currency);
      if (_multi) _seedLines(_ocr.lineItems);
      if (widget.runOcr || _ocr.isPending) {
        WidgetsBinding.instance.addPostFrameCallback(
          (_) => _analyzeWithRetries(),
        );
      }
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        ref.read(confirmClaimLeaveGuardProvider.notifier).state =
            _handleLeaveAttempt;
      }
    });
  }

  /// Fetches a saved draft and seeds every field from it -- the edit-mode counterpart to the
  /// OCR-seeding branch above. Direct `=` assignment throughout (not `??=`), so it always wins
  /// over whatever _loadReferenceData's category fallback already set, regardless of which
  /// async call happens to resolve first.
  Future<void> _loadExistingClaim() async {
    try {
      final claim = await ref.read(apiClientProvider).getClaim(widget.existingClaimId!);
      if (!mounted) return;
      _vendor.text = claim.vendorName ?? '';
      _billNumber.text = claim.billNumber ?? '';
      _amount.text = _money(claim.amount);
      _vat.text = _money(claim.vatAmount);
      _total.text = _money(claim.totalAmount);
      _date.text = claim.billDate ?? '';
      _remarks.text = claim.remarks ?? '';
      _currency = _normalizeCurrency(claim.currency);
      // A saved region wins; a blank draft keeps whatever default reference-data
      // already applied so loading the claim can't wipe Dubai back to empty.
      if (claim.regionCode != null && claim.regionCode!.trim().isNotEmpty) {
        _billRegion = claim.regionCode;
      }
      _applyDefaultBillRegion();
      _categoryId = claim.categoryId;
      _type = claim.type;
      _selectedOp = claim.opNumber == null
          ? null
          : OpportunityResult(opCode: claim.opNumber!, name: claim.opNumber!);
      _editingMulti = claim.isMultiItem;
      if (_editingMulti) _seedLinesFromClaim(claim.lineItems);
      _scheduleQuote();
      _existingReceiptPages = claim.receipt?.pageImageUrls ?? const [];
      _editingDisputed = claim.status == 'disputed';
      _loadedDuplicateWarning = claim.duplicateWarning;
      if (claim.duplicateWarning?.reason == 'same_bill_number') {
        _blockedInvoice = claim.billNumber;
      }
      setState(() => _analyzing = false);
    } catch (e) {
      if (!mounted) return;
      final msg = e.toString();
      setState(() {
        _analyzing = false;
        _error = msg.startsWith('Exception: ') ? msg.substring(11) : msg;
      });
    }
  }

  String _money(double? value) => value == null ? '' : value.toStringAsFixed(2);

  String get _baseCurrency => baseCurrencyForRegion(_billRegion ?? ref.read(authControllerProvider).user?.regionCode);

  bool get _regionLocked => _regions.length <= 1 || _editingDisputed;

  String get _regionHelperText {
    // DropdownMenu shows the helper on one line -- keep these short.
    if (_editingDisputed) return 'Locked once the bill is submitted';
    if (_regions.length <= 1) return 'Your company';
    final current = ref.read(authControllerProvider).user?.regionCode;
    if (widget.existingClaimId == null && current != null && _billRegion == current) {
      // Multi-company users: the default follows the company they're switched to, which
      // may not be where this receipt is from.
      return 'Your current company · change if needed';
    }
    return 'Company this bill is charged to';
  }

  String? _normalizeCurrency(String? value) => normalizeBillCurrency(value);

  /// Prefills Region * from the employee's home company (or the only company
  /// they can pick). A value already on the form / saved draft is left alone.
  /// Must run after `_regions` is known so a lone Dubai assignment actually
  /// shows as selected instead of an empty required dropdown.
  void _applyDefaultBillRegion() {
    final next = defaultBillRegion(
      visibleCodes: [for (final r in _regions) r.regionCode],
      current: _billRegion,
      homeRegion: ref.read(authControllerProvider).user?.regionCode,
    );
    _billRegion = next;
    _ensureRegionOption(next);
  }

  void _ensureRegionOption(String? code) {
    if (code == null || code.isEmpty) return;
    if (_regions.any((r) => r.regionCode == code)) return;
    _regions = [
      ..._regions,
      RegionConfig(id: 0, regionCode: code, regionName: code),
    ];
  }

  Future<void> _loadReferenceData() async {
    try {
      final api = ref.read(apiClientProvider);
      final categories = await api.categories();
      final regions = await api.listRegions();
      final allowed = ref.read(authControllerProvider).user?.allowedRegions ?? const <String>[];
      final visible = allowed.isEmpty
          ? regions
          : regions.where((r) => allowed.contains(r.regionCode)).toList();
      if (mounted) {
        setState(() {
          _categories = categories;
          _regions = visible.isNotEmpty ? List.of(visible) : List.of(regions);
          _applyDefaultBillRegion();
          _categoryId ??=
              _matchExpenseType(categories) ??
              (categories.isNotEmpty ? categories.first.id : null);
          // Lines start in the bill's detected category; the employee can change each one.
          for (final line in _lines) {
            line.categoryId ??= _categoryId;
          }
        });
        _scheduleQuote();
      }
      // Funds are only used for the petty-cash remaining banner -- don't let a
      // slow/failed call keep Region * empty and categories unset.
      try {
        final funds = await api.myFunds();
        if (mounted) setState(() => _myFunds = funds);
      } catch (_) {}
    } catch (_) {}
  }

  int? _matchExpenseType(List<CategoryRef> categories, [String? name]) {
    final wanted = (name ?? _ocr.expenseType)?.toLowerCase();
    if (wanted == null || wanted.isEmpty) return null;
    for (final c in categories) {
      if (c.name.toLowerCase() == wanted) return c.id;
    }
    return null;
  }

  /// Replaces the item drafts with what the scan read (or one empty line if it read none).
  void _seedLines(List<OcrLineItem> items) {
    for (final line in _lines) {
      line.dispose();
    }
    _lines
      ..clear()
      ..addAll(
        items.map((i) => LineItemDraft.fromOcr(i, categoryId: _categoryId)),
      );
    if (_lines.isEmpty) _lines.add(LineItemDraft(categoryId: _categoryId));
    _amountOverridden = false;
  }

  /// Edit-mode counterpart to [_seedLines] -- same shape, seeded from the claim's own saved
  /// lines instead of a fresh OCR read.
  void _seedLinesFromClaim(List<ClaimLineItem> items) {
    for (final line in _lines) {
      line.dispose();
    }
    _lines
      ..clear()
      ..addAll(
        items.map(
          (i) => LineItemDraft(
            description: i.description,
            quantity: i.quantity,
            amount: i.amount,
            vatPercent: i.vatPercent,
            categoryId: i.categoryId,
          ),
        ),
      );
    if (_lines.isEmpty) _lines.add(LineItemDraft(categoryId: _categoryId));
    // When loading an existing claim, _amount is already populated from the saved value
    // (set by _loadExistingClaim before this is called) -- treat it as user-set.
    _amountOverridden = true;
  }

  double get _linesTotal =>
      _lines.fold(0.0, (sum, l) => sum + (l.amountValue ?? 0));

  double get _vatValue => double.tryParse(_vat.text.trim()) ?? 0;

  void _syncAmountExclVat() {
    final excl = _linesTotal - _vatValue;
    _amount.text = excl < 0 ? '' : excl.toStringAsFixed(2);
  }

  /// Live, not just after a save -- lets the employee see what's still blocking a real submit
  /// while they're still editing a draft.
  List<String> get _stillMissingForSubmit => missingForSubmit(
    total: double.tryParse(_total.text.trim()),
    currency: _currency,
    vendorText: _vendor.text,
    billDateText: _date.text,
    billNumberText: _billNumber.text,
    regionCode: _billRegion,
  );

  /// Claim-level category for a multi-item bill: the category carrying the most money.
  int? get _mainLineCategory {
    final byCategory = <int, double>{};
    for (final l in _lines) {
      final c = l.categoryId;
      if (c != null) {
        byCategory[c] = (byCategory[c] ?? 0) + (l.amountValue ?? 0);
      }
    }
    if (byCategory.isEmpty) return null;
    return byCategory.entries.reduce((a, b) => b.value > a.value ? b : a).key;
  }

  void _startTicker() {
    _ticker?.cancel();
    _ticker = Timer.periodic(const Duration(milliseconds: 400), (_) {
      if (!mounted || !_analyzing) return;
      setState(() {
        if (_progress < 88) _progress += _progress < 40 ? 4 : 2;
      });
    });
  }

  Future<void> _analyzeWithRetries({int maxAttempts = _maxOcrAttempts}) async {
    setState(() {
      _analyzing = true;
      _ocrFailed = false;
      _progress = 8;
    });
    _startTicker();

    // GPT is a paid call that fails for reasons a silent retry won't fix (no key, credit,
    // timeout) -- show the error once; the banner's Retry button is there if the employee wants it.
    Object? lastError;
    for (var i = 1; i <= maxAttempts; i++) {
      if (!mounted) return;
      if (i > 1) {
        setState(() => _progress = 20);
      }
      try {
        final result = await ref
            .read(apiClientProvider)
            .analyzeReceipt(_ocr.receiptId, mode: widget.ocrMode);
        if (!mounted) return;
        _applyOcr(result);
        _ticker?.cancel();
        setState(() {
          _analyzing = false;
          _ocrFailed = false;
          _progress = 100;
        });
        return;
      } catch (e) {
        lastError = e;
        if (i < maxAttempts) {
          await Future<void>.delayed(const Duration(seconds: 1));
        }
      }
    }

    if (!mounted) return;
    _ticker?.cancel();
    setState(() {
      _analyzing = false;
      _ocrFailed = true;
      _progress = 0;
      _error = "Couldn't read this bill. Try again.";
    });
  }

  void _applyOcr(OcrResult result) {
    _ocr = result;
    _vendor.text = result.vendor.trim();
    if (_billNumber.text.isEmpty) _billNumber.text = result.billNumber ?? '';
    _amount.text = _money(result.amount);
    _vat.text = _money(result.vatAmount);
    _total.text = _money(result.totalAmount);
    _date.text = result.date;
    _currency = _normalizeCurrency(result.currency);
    _scheduleQuote();
    final matched = _matchExpenseType(_categories, result.expenseType);
    if (matched != null) _categoryId = matched;
    if (_multi) _seedLines(result.lineItems);
    if (result.duplicateWarning?.reason == 'same_bill_number') {
      _blockedInvoice = result.billNumber;
    }
  }

  @override
  void dispose() {
    // Not cleared here: using `ref` during dispose isn't safe (Riverpod asserts against it once
    // the element is unmounting). A stale reference left in the provider is harmless -- the
    // first line of _handleLeaveAttempt checks `mounted` and treats a disposed screen as nothing
    // left to protect, and the next ConfirmClaimScreen that mounts overwrites it anyway.
    _ticker?.cancel();
    _amount.removeListener(_onMoneyFieldsChanged);
    _vat.removeListener(_onMoneyFieldsChanged);
    _total.removeListener(_onMoneyFieldsChanged);
    _vendor.dispose();
    _billNumber.dispose();
    _amount.dispose();
    _vat.dispose();
    _total.dispose();
    _date.dispose();
    _remarks.dispose();
    for (final line in _lines) {
      line.dispose();
    }
    super.dispose();
  }

  Future<void> _submit({required bool asDraft, bool navigateOnSuccess = true}) async {
    if (_analyzing) return;
    setState(() {
      _busy = true;
      // Which button's label/spinner should reflect the busy state -- _busy alone doesn't say
      // whether this is a Submit or a Save as draft in flight, which previously made the
      // Submit button flash "Submitting…" even when Save as draft was the one pressed.
      _busyAsDraft = asDraft;
      _error = null;
    });
    try {
      List<Map<String, dynamic>>? lineItems;
      if (_multi) {
        if (_lines.isEmpty) throw Exception('Add at least one item');
        final incomplete = _lines.indexWhere((l) => l.problem != null);
        if (incomplete >= 0) {
          setState(() => _showLineProblems = true);
          throw Exception(
            'Item ${incomplete + 1}: ${_lines[incomplete].problem}',
          );
        }
        lineItems = _lines.map((l) => l.toJson()).toList();
        // Totals come from the lines (the backend recomputes them the same way).
        final total = double.parse(_linesTotal.toStringAsFixed(2));
        if (_vatValue > total) {
          throw Exception("VAT can’t be more than the items total");
        }
        _total.text = total.toStringAsFixed(2);
        // If user hasn’t manually set Amount excl. VAT, fill it now.
        if (!_amountOverridden || _amount.text.trim().isEmpty) {
          _amount.text = (total - _vatValue).toStringAsFixed(2);
        }
        _categoryId = _mainLineCategory ?? _categoryId;
      }
      final amount = double.tryParse(_amount.text.trim());
      final vatText = _vat.text.trim();
      final vat = vatText.isEmpty ? 0.0 : double.tryParse(vatText);
      final totalText = _total.text.trim();
      double? total = totalText.isEmpty ? null : double.tryParse(totalText);
      if (totalText.isNotEmpty && total == null) {
        throw ClaimFieldError('Enter a valid total amount');
      }
      validateClaimFields(
        asDraft: asDraft,
        amount: amount,
        categoryId: _categoryId,
        vat: vat,
        total: total,
        currency: _currency,
        vendorText: _vendor.text,
        billDateText: _date.text,
        billNumberText: _billNumber.text,
        regionCode: _billRegion,
      );
      if (!asDraft && _missingProject) {
        throw ClaimFieldError(
          _multi
              ? 'Enter the project OP code for the bill, or for every item.'
              : 'Enter the project OP code for this bill.',
        );
      }
      if (!asDraft && _pettyCashBlocksSubmit) {
        throw ClaimFieldError(_pettyCashBlockMessage);
      }
      if (!asDraft) {
        final clash = _ocr.duplicateWarning ?? _loadedDuplicateWarning;
        final typed = _billNumber.text.trim().toLowerCase();
        final blocked = (_blockedInvoice ?? '').trim().toLowerCase();
        if (clash?.reason == 'same_bill_number' &&
            typed.isNotEmpty &&
            typed == blocked) {
          throw ClaimFieldError(clash!.message);
        }
      }
      if (!asDraft &&
          !await _confirmBeforeSubmit(amount: amount!, vat: vat!, total: total!)) {
        return;
      }
      final api = ref.read(apiClientProvider);
      final body = {
        'vendor': _vendor.text.trim(),
        'amount': amount,
        'vat_amount': vat,
        'total_amount': ?total,
        'currency': ?_currency,
        'bill_date': _date.text.trim().isEmpty ? null : _date.text.trim(),
        'category_id': _categoryId,
        'type': _type,
        'project_id': null,
        'op_number': _selectedOp?.opCode,
        // bill_number is a required field server-side, but has no length constraint -- an empty
        // string is a valid "not filled in yet" draft value; only a real submit forces it above.
        'bill_number': _billNumber.text.trim(),
        'remarks': _remarks.text.trim().isEmpty ? null : _remarks.text.trim(),
        'line_items': ?lineItems,
        'region_code': ?_billRegion,
      };
      ExpenseClaim claim;
      if (widget.existingClaimId != null) {
        final id = widget.existingClaimId!;
        await api.updateDraft(id, body);
        try {
          claim = asDraft
              ? await api.getClaim(id)
              : _editingDisputed
                  ? await api.resubmitClaim(id)
                  : await api.submitClaim(id);
        } catch (e) {
          // The edit itself is already saved server-side at this point -- only the submit step
          // failed (e.g. the backend's own completeness check). Don't lose that: reload the
          // persisted (updated) state and stay here so the employee can fix whatever's missing,
          // instead of bouncing to the read-only detail screen as if nothing happened.
          if (mounted) {
            final msg = e.toString();
            setState(() => _error = msg.startsWith('Exception: ') ? msg.substring(11) : msg);
          }
          return;
        }
      } else {
        claim = await api.createClaim({
          ...body,
          // Submit always has one (validated above). A draft without one is parked under the
          // signed-in company by the server -- never a hard-coded company.
          'region_code': ?_billRegion,
          'receipt_id': _ocr.receiptId,
          's3_key': _ocr.s3Key,
          'submit': !asDraft,
        });
      }
      if (!mounted) return;
      if (claim.duplicateWarning != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(claim.duplicateWarning!.message)),
        );
      }
      if (navigateOnSuccess) {
        context.go('/claim/${claim.id}');
      }
    } catch (e) {
      final msg = e.toString();
      setState(() => _error = msg.startsWith('Exception: ') ? msg.substring(11) : msg);
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
          _busyAsDraft = null;
        });
      }
    }
  }

  /// "Please cross-check" box shown on Submit for approval: the key figures the employee is about to
  /// send, plus anything that looks off (items don't add up to the printed total, odd quantities,
  /// amount + VAT not equal to total). Returns true only if they confirm.
  Future<bool> _confirmBeforeSubmit({
    required double amount,
    required double vat,
    required double total,
  }) async {
    final cur = _currency ?? '';
    String m(double v) => '$cur ${v.toStringAsFixed(2)}'.trim();
    final printed = _ocrFailed ? null : _ocr.totalAmount;
    final warnings = <String>[];
    if (_multi) {
      if (printed != null && (printed - total).abs() > 0.01) {
        warnings.add(
          'Items add up to ${m(total)} but the bill’s printed total is ${m(printed)} '
          '(difference ${m((printed - total).abs())}). An item may be missing or misread.',
        );
      }
      final oddQty = _lines.where((l) => l.quantityLooksOff).length;
      if (oddQty > 0) {
        warnings.add(
          '$oddQty item${oddQty == 1 ? ' has' : 's have'} a decimal quantity. '
          'Check it isn’t a rate or VAT % read as the quantity.',
        );
      }
    } else if ((amount + vat - total).abs() > 0.01) {
      warnings.add(
        'Amount (${m(amount)}) + VAT (${m(vat)}) doesn’t equal the total (${m(total)}).',
      );
    }

    Widget row(String label, String value) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 104,
            child: Text(
              label,
              style: const TextStyle(color: AppColors.textSecondary),
            ),
          ),
          Expanded(
            child: Text(
              value.isEmpty ? '—' : value,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Please cross-check before submitting'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'These details were read from the bill automatically and can contain mistakes. '
                'Compare them with the bill before you send it for approval.',
              ),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.lightBlue,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  children: [
                    row('Vendor', _vendor.text.trim()),
                    row('Bill no.', _billNumber.text.trim()),
                    row('Date', _date.text.trim()),
                    row('Bill currency', _currency ?? ''),
                    if (_multi) row('Items', '${_lines.length}'),
                    row('Amount excl. VAT', m(amount)),
                    row('VAT', m(vat)),
                    row('Total', m(total)),
                    if ((_currency ?? '').toUpperCase() != _baseCurrency && _rateToBase != null)
                      row('In $_baseCurrency', formatMoney(_baseCurrency, total * _rateToBase!)),
                  ],
                ),
              ),
              for (final w in warnings) ...[
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.warningSoft,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.orange),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        PhosphorIcons.warning(),
                        size: 18,
                        color: AppColors.orange,
                      ),
                      const SizedBox(width: 8),
                      Expanded(child: Text(w)),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
        actions: [
          TextButton(
            style: TextButton.styleFrom(
              backgroundColor: AppColors.lightBlue,
              foregroundColor: AppColors.darkBlue,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Go back and check'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Looks right, submit'),
          ),
        ],
      ),
    );
    return ok ?? false;
  }

  /// Shown before leaving this screen by any route -- the system/app-bar back button, or a
  /// bottom-nav tab tap routed through [confirmClaimLeaveGuardProvider] -- so an employee never
  /// accidentally loses a claim the app already spent OCR work reading off the bill.
  /// Returns true if the caller should go ahead with its own navigation -- including after a
  /// successful "Save as draft", which saves silently and lets the original navigation (the tab
  /// tap, or the back press) continue to where it was actually headed; false if the user chose
  /// to keep editing, or if the save failed and this screen needs to stay up to show the error.
  Future<bool> _handleLeaveAttempt() async {
    // A stale registration from an already-disposed screen (see dispose() above) -- nothing
    // left here to protect, so let the navigation that triggered this proceed.
    if (!mounted) return true;
    if (_busy) return false;
    // A second exit attempt (another nav tap, or the back button) while the dialog from a first
    // one is still resolving -- don't stack a second dialog on top of it. The first attempt is
    // already deciding this screen's fate, so this one just declines to navigate.
    if (_leaveAttemptInProgress) return false;
    _leaveAttemptInProgress = true;
    try {
      return await _resolveLeaveAttempt();
    } finally {
      if (mounted) _leaveAttemptInProgress = false;
    }
  }

  Future<bool> _resolveLeaveAttempt() async {
    final action = await showDialog<_LeaveAction>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Leave without saving?'),
        content: const Text('Leaving now without saving will lose these changes.'),
        actions: [
          TextButton(
            style: TextButton.styleFrom(
              backgroundColor: AppColors.lightBlue,
              foregroundColor: AppColors.darkBlue,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            onPressed: () => Navigator.pop(ctx, _LeaveAction.cancel),
            child: const Text('Keep editing'),
          ),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: AppColors.danger),
            onPressed: () => Navigator.pop(ctx, _LeaveAction.discard),
            child: const Text('Discard'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, _LeaveAction.saveDraft),
            child: const Text('Save as draft'),
          ),
        ],
      ),
    );
    switch (action) {
      case _LeaveAction.saveDraft:
        await _submit(asDraft: true, navigateOnSuccess: false);
        // On failure _submit() sets _error and the screen must stay put so it's visible.
        if (_error != null) return false;
        _clearLeaveGuard();
        // On success there's nothing left to protect -- let the navigation that triggered
        // this guard (the tab tap, or the back press) continue to where it was actually headed,
        // instead of redirecting to the claim detail screen nobody asked to see.
        return true;
      case _LeaveAction.discard:
        _clearLeaveGuard();
        return true;
      case _LeaveAction.cancel:
      case null:
        return false;
    }
  }

  /// Some destinations this guard protects against (e.g. the notification bell, which
  /// `context.push`es on top instead of replacing this route) never actually pop/dispose this
  /// screen -- it stays mounted underneath, so the `mounted`-check at the top of
  /// [_handleLeaveAttempt] alone can't tell a resolved leave apart from a fresh one. Once the
  /// employee has explicitly discarded or saved, clear this screen's own registration so a
  /// second navigation attempt from the same still-mounted instance doesn't re-ask about a claim
  /// that's already been dealt with.
  void _clearLeaveGuard() {
    if (ref.read(confirmClaimLeaveGuardProvider) == _handleLeaveAttempt) {
      ref.read(confirmClaimLeaveGuardProvider.notifier).state = null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final currency = _currency;
    final fieldsLocked = _analyzing;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        final shouldLeave = await _handleLeaveAttempt();
        if (shouldLeave && mounted) {
          Navigator.of(context).pop();
        }
      },
      child: Scaffold(
      appBar: BrandAppBar(
        title: widget.existingClaimId != null
            ? (_editingDisputed ? 'Correct claim' : 'Edit draft')
            : 'Confirm claim',
        automaticallyImplyLeading: true,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          if (widget.localPaths.isNotEmpty)
            ReceiptPagesView.local(widget.localPaths, height: 200)
          else if (_existingReceiptPages.isNotEmpty)
            ReceiptPagesView.network(_existingReceiptPages, height: 200),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerLeft,
            child: Chip(
              avatar: Icon(
                _multi ? PhosphorIcons.listBullets() : PhosphorIcons.receipt(),
                size: 18,
                color: AppColors.darkBlue,
              ),
              label: Text(_multi ? BillLineMode.multiple.label : BillLineMode.single.label),
              visualDensity: VisualDensity.compact,
            ),
          ),
          if (_analyzing) ...[
            const SizedBox(height: 12),
            widget.existingClaimId != null
                ? const _LoadingDraftIndicator()
                : _OcrProgress(
                    progress: _progress,
                    label: 'Scanning…',
                  ),
          ],
          if (_ocrFailed) ...[
            const SizedBox(height: 12),
            _ManualEntryBanner(
              onRetry: _analyzing
                  ? null
                  : () => _analyzeWithRetries(maxAttempts: 1),
            ),
          ],
          if ((_ocr.duplicateWarning ?? _loadedDuplicateWarning) != null) ...[
            const SizedBox(height: 12),
            _notice((_ocr.duplicateWarning ?? _loadedDuplicateWarning)!.message),
          ],
          // Only shown once amount, VAT, and total are ALL present — a field that wasn't extracted isn't a real mismatch, it's missing data.
          if (_ocr.reconciliationMismatch &&
              _ocr.amount != null &&
              _ocr.vatAmount != null &&
              _ocr.totalAmount != null) ...[
            const SizedBox(height: 12),
            _notice(
              "Amount + VAT doesn't match the total on this bill — please double-check these figures before submitting.",
            ),
          ],
          const SizedBox(height: 16),
          if (!_analyzing)
            const Padding(
              padding: EdgeInsets.only(bottom: 16),
              child: Text(
                'Review every field before submitting. You can edit every value.',
              ),
            ),
          IgnorePointer(
            ignoring: fieldsLocked,
            child: Opacity(
              opacity: fieldsLocked ? 0.55 : 1,
              child: Column(
                children: [
                  _OcrTextField(
                    controller: _vendor,
                    label: 'Vendor / customer name',
                    lowConfidence: !_ocrFailed && _ocr.isLow('vendor'),
                    confidence: _ocrFailed
                        ? null
                        : _ocr.confidenceFor('vendor'),
                    allowArabic: true,
                  ),
                  const SizedBox(height: 12),
                  _OcrTextField(
                    controller: _billNumber,
                    label: 'Bill / invoice number *',
                    lowConfidence: !_ocrFailed && _ocr.isLow('invoice_number'),
                    confidence: _ocrFailed
                        ? null
                        : (_ocr.confidenceFor('invoice_number') ?? _ocr.confidenceFor('transaction_number')),
                  ),
                  const SizedBox(height: 12),
                  _BillCurrencyFields(
                    currency: _currency,
                    choices: billCurrencyChoices(_currency),
                    baseCurrency: _baseCurrency,
                    onCurrencyChanged: (v) {
                      setState(() => _currency = v);
                      _scheduleQuote();
                    },
                  ),
                  const SizedBox(height: 12),
                  // DropdownMenu (not DropdownButtonFormField): its list always opens below the
                  // field, instead of over it aligned to the selected item.
                  DropdownMenu<String>(
                    // Rebuilt when the selection or the company list changes, since
                    // initialSelection is only read once.
                    key: ValueKey('region-$_billRegion-${_regions.length}-$_regionLocked'),
                    initialSelection: _regions.any((r) => r.regionCode == _billRegion) ? _billRegion : null,
                    expandedInsets: EdgeInsets.zero,
                    label: const Text('Region *'),
                    helperText: _regionHelperText,
                    requestFocusOnTap: false,
                    // Locked when there's nothing to choose, and once the bill has been
                    // submitted: approvals already given belong to that company's approvers.
                    enabled: !_regionLocked,
                    dropdownMenuEntries: [
                      for (final r in _regions)
                        // Short names (Dubai, UAE, KSA, Oman), same as the side-menu switcher.
                        DropdownMenuEntry(value: r.regionCode, label: companyLabel(r.regionCode)),
                    ],
                    onSelected: (v) {
                      if (v == null || v == _billRegion) return;
                      setState(() => _billRegion = v);
                      _scheduleQuote();
                    },
                  ),
                  _ConvertedAmountCard(
                    billCurrency: (_currency ?? '').toUpperCase(),
                    baseCurrency: _baseCurrency,
                    billTotal: _claimAmount,
                    rate: _rateToBase,
                    failed: _quoteFailed,
                  ),
                  if (_multi) ...[
                    const SizedBox(height: 16),
                    _SectionLabel(
                      'Items on this bill',
                      trailing:
                          '${_lines.length} item${_lines.length == 1 ? '' : 's'}',
                    ),
                    const SizedBox(height: 8),
                    LineItemsEditor(
                      lines: _lines,
                      categories: _categories,
                      currency: currency,
                      showProblems: _showLineProblems,
                      ownDepartmentId: ref.read(authControllerProvider).user?.departmentId,
                      pettyCash: _type == 'petty_cash',
                      splitsByDepartment: !_employeeAdvances && !_sitePots,
                      onChanged: () => setState(() {
                        if (!_amountOverridden) _syncAmountExclVat();
                      }),
                      onAdd: () => setState(
                        () => _lines.add(
                          LineItemDraft(
                            categoryId: _categoryId,
                            // Defaults to the line above it, falling back to the
                            // claim-level OP, so splitting one item off a mostly
                            // one-project bill is the only line that needs editing.
                            opResult: _lines.isNotEmpty
                                ? _lines.last.opResult ?? _selectedOp
                                : _selectedOp,
                          ),
                        ),
                      ),
                      onRemove: (i) =>
                          setState(() => _lines.removeAt(i).dispose()),
                    ),
                    const SizedBox(height: 12),
                    _OcrTextField(
                      controller: _amount,
                      label: currency == null
                          ? 'Amount excl. VAT'
                          : 'Amount excl. VAT ($currency)',
                      lowConfidence: false,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      inputFormatters: _decimalInputFormatters,
                      onChanged: () => setState(() => _amountOverridden = true),
                    ),
                    const SizedBox(height: 12),
                    _OcrTextField(
                      controller: _vat,
                      label:
                          'VAT amount included in the items (leave blank if none)',
                      lowConfidence: !_ocrFailed && _ocr.isLow('vat_amount'),
                      confidence: _ocrFailed
                          ? null
                          : _ocr.confidenceFor('vat_amount'),
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      inputFormatters: _decimalInputFormatters,
                      onChanged: () => setState(() {
                        if (!_amountOverridden) _syncAmountExclVat();
                      }),
                    ),
                    const SizedBox(height: 12),
                    _ItemsTotals(
                      currency: currency,
                      amountExclVat: double.tryParse(_amount.text.trim()) ?? (_linesTotal - _vatValue),
                      vat: _vatValue,
                      itemsTotal: _linesTotal,
                      billTotal: _ocrFailed ? null : _ocr.totalAmount,
                      baseCurrency: _baseCurrency,
                      rateToBase: _rateToBase,
                    ),
                  ],
                  if (!_multi) ...[
                    const SizedBox(height: 12),
                    _OcrTextField(
                      controller: _amount,
                      label: currency == null
                          ? 'Amount (excl. VAT) *'
                          : 'Amount excl. VAT ($currency) *',
                      lowConfidence: !_ocrFailed && _ocr.isLow('amount'),
                      confidence: _ocrFailed
                          ? null
                          : _ocr.confidenceFor('amount'),
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      inputFormatters: _decimalInputFormatters,
                    ),
                    const SizedBox(height: 12),
                    _OcrTextField(
                      controller: _vat,
                      label: 'VAT amount (leave blank if none)',
                      lowConfidence: !_ocrFailed && _ocr.isLow('vat_amount'),
                      confidence: _ocrFailed
                          ? null
                          : _ocr.confidenceFor('vat_amount'),
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      inputFormatters: _decimalInputFormatters,
                    ),
                    const SizedBox(height: 12),
                    _OcrTextField(
                      controller: _total,
                      label: currency == null
                          ? 'Total amount *'
                          : 'Total amount ($currency) *',
                      lowConfidence: !_ocrFailed && _ocr.isLow('total_amount'),
                      confidence: _ocrFailed
                          ? null
                          : _ocr.confidenceFor('total_amount'),
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      inputFormatters: _decimalInputFormatters,
                    ),
                  ],
                  const SizedBox(height: 12),
                  _OcrTextField(
                    controller: _date,
                    label: 'Bill date *',
                    lowConfidence: !_ocrFailed && _ocr.isLow('date'),
                    confidence: _ocrFailed ? null : _ocr.confidenceFor('date'),
                  ),
                  // Multi-item bills carry a category per line instead of one for the whole bill.
                  if (!_multi) ...[
                    const SizedBox(height: 12),
                    _flaggedDecorator(
                      label: 'Expense type *',
                      low: !_ocrFailed && _ocr.isLow('expense_type'),
                      confidence: _ocrFailed
                          ? null
                          : _ocr.confidenceFor('expense_type'),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<int>(
                          isExpanded: true,
                          value: _categoryId,
                          items: _categories
                              .map(
                                (c) => DropdownMenuItem(
                                  value: c.id,
                                  child: Text(c.name),
                                ),
                              )
                              .toList(),
                          onChanged: (v) => setState(() => _categoryId = v),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          InputDecorator(
            decoration: const InputDecoration(labelText: 'Claim type *'),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                isExpanded: true,
                value: _type,
                items: const [
                  DropdownMenuItem(
                    value: 'reimbursement',
                    child: Text('Reimbursement'),
                  ),
                  DropdownMenuItem(
                    value: 'petty_cash',
                    child: Text('Petty cash'),
                  ),
                ],
                onChanged: (v) => setState(() => _type = v ?? 'reimbursement'),
              ),
            ),
          ),
          if (_type == 'petty_cash') ...[
            const SizedBox(height: 8),
            _PotLimitBanner(
              fund: _potForBill,
              usable: _potForBill == null ? null : _usableFor(_potForBill!),
              blocked: _pettyCashBlocksSubmit,
              message: _pettyCashBlocksSubmit
                  ? _pettyCashBlockMessage
                  : null,
            ),
          ],
          if (_otherDepartmentNote != null) ...[
            const SizedBox(height: 8),
            Text(
              _otherDepartmentNote!,
              style: const TextStyle(fontSize: 12.5, color: AppColors.darkBlue, fontWeight: FontWeight.w600),
            ),
          ],
          const SizedBox(height: 12),
          OpCodeField(
            // Professional Signs: every bill names its project (for the project-wise report).
            label: _sitePots ? 'Site (project OP code) *' : (_employeeAdvances ? 'Project / OP code *' : 'Project / OP code'),
            initial: _selectedOp,
            onResolved: (v) => setState(() => _selectedOp = v),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _remarks,
            maxLines: 2,
            decoration: const InputDecoration(labelText: 'Remarks (optional)'),
          ),
          if (_stillMissingForSubmit.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(
              'Still needed to submit: ${_stillMissingForSubmit.join(', ')}.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 12),
            ),
          ],
          if (_error != null && !_ocrFailed) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          const SizedBox(height: 20),
          FilledButton(
            onPressed: (_busy || _analyzing || _pettyCashBlocksSubmit)
                ? null
                : () => _submit(asDraft: false),
            child: Text(
              _busyAsDraft == false
                  ? 'Submitting…'
                  : _analyzing
                  ? 'Waiting for bill reading…'
                  : 'Submit for approval',
            ),
          ),
          const SizedBox(height: 10),
          OutlinedButton(
            onPressed: (_busy || _analyzing)
                ? null
                : () => _submit(asDraft: true),
            child: Text(_busyAsDraft == true ? 'Saving…' : 'Save as draft'),
          ),
        ],
      ),
      ),
    );
  }

  Widget _notice(String text) {
    return Material(
      color: AppColors.warningSoft,
      borderRadius: BorderRadius.circular(12),
      child: Padding(padding: const EdgeInsets.all(12), child: Text(text)),
    );
  }
}

/// Shown while an existing draft is being fetched -- the edit-mode counterpart to
/// [_OcrProgress], deliberately plain (no percentage, no "reading the bill" framing) since
/// nothing is being read off the bill again, just loaded from what's already saved.
class _LoadingDraftIndicator extends StatelessWidget {
  const _LoadingDraftIndicator();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.only(top: 12),
      child: Row(
        children: [
          SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          SizedBox(width: 10),
          Text(
            'Loading draft…',
            style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.darkBlue),
          ),
        ],
      ),
    );
  }
}

class _OcrProgress extends StatelessWidget {
  const _OcrProgress({required this.progress, this.label});

  final int progress;
  final String? label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Column(
        children: [
          Row(
            children: [
              const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
              const SizedBox(width: 10),
              Text(
                '$progress%',
                style: const TextStyle(
                  fontWeight: FontWeight.w700,
                  color: AppColors.darkBlue,
                ),
              ),
              if (label != null) ...[
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    label!,
                    style: const TextStyle(color: AppColors.textSecondary),
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(99),
            child: LinearProgressIndicator(
              value: (progress.clamp(0, 100)) / 100,
              minHeight: 8,
              backgroundColor: AppColors.lightBlue,
              color: AppColors.brightBlue,
            ),
          ),
        ],
      ),
    );
  }
}

class _ManualEntryBanner extends StatelessWidget {
  const _ManualEntryBanner({this.onRetry, this.detail});

  final VoidCallback? onRetry;

  final String? detail;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.warningSoft,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Couldn’t read this bill. Enter the details below.',
                    style: TextStyle(fontWeight: FontWeight.w600, height: 1.3),
                  ),
                  if (detail != null && detail!.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(detail!, style: const TextStyle(height: 1.3)),
                  ],
                ],
              ),
            ),
            if (onRetry != null) ...[
              const SizedBox(width: 8),
              OutlinedButton(
                onPressed: onRetry,
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.darkBlue,
                  side: const BorderSide(color: AppColors.darkBlue),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 8,
                  ),
                  minimumSize: Size.zero,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  visualDensity: VisualDensity.compact,
                ),
                child: const Text(
                  'Recheck once more',
                  style: TextStyle(fontSize: 12),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

InputDecoration _ocrDecoration({
  required String label,
  required bool low,
  double? confidence,
}) {
  return InputDecoration(
    labelText: label,
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: BorderSide(
        color: low ? AppColors.orange : AppColors.divider,
        width: low ? 1.6 : 1,
      ),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: BorderSide(
        color: low ? AppColors.orange : AppColors.darkBlue,
        width: 1.5,
      ),
    ),
    filled: true,
    fillColor: low ? AppColors.warningSoft : AppColors.card,
  );
}

class _OcrTextField extends StatefulWidget {
  const _OcrTextField({
    required this.controller,
    required this.label,
    required this.lowConfidence,
    this.confidence,
    this.keyboardType,
    this.allowArabic = false,
    this.inputFormatters,
    this.onChanged,
  });

  final TextEditingController controller;
  final String label;
  final bool lowConfidence;
  final double? confidence;
  final TextInputType? keyboardType;
  final bool allowArabic;
  final List<TextInputFormatter>? inputFormatters;
  final VoidCallback? onChanged;

  @override
  State<_OcrTextField> createState() => _OcrTextFieldState();
}

class _OcrTextFieldState extends State<_OcrTextField> {
  @override
  Widget build(BuildContext context) {
    final arabic =
        widget.allowArabic && _isArabicDominant(widget.controller.text);
    return TextField(
      controller: widget.controller,
      keyboardType: widget.keyboardType ?? TextInputType.text,
      textCapitalization: widget.allowArabic
          ? TextCapitalization.sentences
          : TextCapitalization.none,
      textDirection: arabic ? TextDirection.rtl : TextDirection.ltr,
      inputFormatters: widget.inputFormatters,
      onChanged: (_) {
        if (widget.allowArabic) setState(() {});
        widget.onChanged?.call();
      },
      decoration: _ocrDecoration(
        label: widget.label,
        low: widget.lowConfidence,
        confidence: widget.confidence,
      ),
    );
  }
}

/// "Converted: AED 978.20" under the company picker when the bill isn't in the company's
/// base currency. Employees see only the amount; the rate is shown to approvers.
class _ConvertedAmountCard extends StatelessWidget {
  const _ConvertedAmountCard({
    required this.billCurrency,
    required this.baseCurrency,
    required this.billTotal,
    required this.rate,
    required this.failed,
  });

  final String billCurrency;
  final String baseCurrency;
  final double billTotal;
  final double? rate;
  final bool failed;

  @override
  Widget build(BuildContext context) {
    if (billCurrency.isEmpty || billCurrency == baseCurrency) return const SizedBox.shrink();
    final r = rate;
    final String headline;
    String? detail;
    if (r == null) {
      headline = 'Converted to $baseCurrency at submit';
      detail = failed ? null : 'Loading…';
    } else {
      headline = 'Converted: ${formatMoney(baseCurrency, billTotal * r)}';
    }
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.lightBlue,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(headline, style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.darkBlue)),
            if (detail != null) ...[
              const SizedBox(height: 4),
              Text(detail, style: const TextStyle(fontSize: 12.5, color: AppColors.textSecondary)),
            ],
          ],
        ),
      ),
    );
  }
}

class _BillCurrencyFields extends StatelessWidget {
  const _BillCurrencyFields({
    required this.currency,
    required this.choices,
    required this.baseCurrency,
    required this.onCurrencyChanged,
  });

  final String? currency;
  final List<String> choices;
  final String baseCurrency;
  final ValueChanged<String?> onCurrencyChanged;

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<String>(
      value: currency != null && choices.contains(currency) ? currency : null,
      decoration: const InputDecoration(
        labelText: 'Bill currency *',
        helperText: 'Currency printed on the receipt',
      ),
      items: [
        for (final code in choices)
          DropdownMenuItem(
            value: code,
            child: Text(code == baseCurrency ? '$code (region base)' : code),
          ),
      ],
      onChanged: onCurrencyChanged,
    );
  }
}

Widget _flaggedDecorator({
  required String label,
  required bool low,
  required double? confidence,
  required Widget child,
}) {
  return InputDecorator(
    decoration: _ocrDecoration(label: label, low: low, confidence: confidence),
    child: child,
  );
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.text, {this.trailing});

  final String text;
  final String? trailing;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(
          text,
          style: const TextStyle(
            fontWeight: FontWeight.w700,
            fontSize: 15,
            color: AppColors.textPrimary,
          ),
        ),
        const Spacer(),
        if (trailing != null)
          Text(
            trailing!,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 13,
            ),
          ),
      ],
    );
  }
}

/// Totals computed from the item lines, compared with the total printed on the bill.
class _ItemsTotals extends StatelessWidget {
  const _ItemsTotals({
    required this.currency,
    required this.amountExclVat,
    required this.vat,
    required this.itemsTotal,
    this.billTotal,
    this.baseCurrency,
    this.rateToBase,
  });

  final String? currency;
  final double amountExclVat;
  final double vat;
  final double itemsTotal; // line items sum — only used for the mismatch warning
  final double? billTotal;
  // The bill's company currency and today's rate (1 bill unit = rateToBase base units);
  // rateToBase is null while the rate is still loading or couldn't be fetched.
  final String? baseCurrency;
  final double? rateToBase;

  String _m(double v) => '${currency ?? ''} ${v.toStringAsFixed(2)}'.trim();

  bool get _foreign {
    final bill = (currency ?? '').toUpperCase();
    final base = (baseCurrency ?? '').toUpperCase();
    return bill.isNotEmpty && base.isNotEmpty && bill != base;
  }

  @override
  Widget build(BuildContext context) {
    final displayTotal = amountExclVat + vat;
    final mismatch =
        billTotal != null && (billTotal! - displayTotal).abs() > 0.01;
    Widget row(String label, String value, {bool bold = false}) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              style: TextStyle(
                color: bold ? AppColors.textPrimary : AppColors.textSecondary,
              ),
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontWeight: bold ? FontWeight.w700 : FontWeight.w500,
              fontSize: bold ? 16 : 14,
            ),
          ),
        ],
      ),
    );
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.lightBlue,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          row("Amount excl. VAT", _m(amountExclVat)),
          row("VAT", _m(vat)),
          const Divider(height: 14),
          row("Total", _m(displayTotal), bold: true),
          if (_foreign) ...[
            const Divider(height: 14),
            if (rateToBase != null) ...[
              row("Total in $baseCurrency", formatMoney(baseCurrency!, displayTotal * rateToBase!), bold: true),
            ] else
              Text(
                "Converted to $baseCurrency at submit",
                style: const TextStyle(fontSize: 12.5, color: AppColors.textSecondary),
              ),
          ],
          if (mismatch) ...[
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.warningSoft,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.orange),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(PhosphorIcons.warning(), size: 18, color: AppColors.orange),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      "Items don’t match the bill. The printed total is ${_m(billTotal!)}, the total here is ${_m(displayTotal)} (difference ${_m((billTotal! - displayTotal).abs())}). Check the items: one may be missing or misread.",
                      style: const TextStyle(fontSize: 12.5, height: 1.35),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _PotLimitBanner extends StatelessWidget {
  const _PotLimitBanner({
    required this.fund,
    required this.usable,
    required this.blocked,
    this.message,
  });

  final PettyCashFund? fund;
  final double? usable;
  final bool blocked;
  final String? message;

  @override
  Widget build(BuildContext context) {
    final left = fund == null || usable == null
        ? null
        : formatMoney(fund!.currency, usable!);
    final text = blocked
        ? (message ?? 'This bill exceeds available petty cash.')
        : '$left left';
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: blocked ? const Color(0xFFFFEBEE) : AppColors.lightBlue,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w700,
          color: blocked ? AppColors.danger : AppColors.textPrimary,
        ),
      ),
    );
  }
}

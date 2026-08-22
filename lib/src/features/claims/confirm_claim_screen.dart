import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/image_preview_screen.dart';

final _arabic = RegExp(r'[\u0600-\u06FF]');

const _maxOcrAttempts = 2;

// keyboardType only hints the on-screen keyboard, so this is the actual enforcement: at most one decimal point, digits only otherwise.
final _decimalInputFormatters = <TextInputFormatter>[
  FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d{0,2}')),
];

class ConfirmClaimScreen extends ConsumerStatefulWidget {
  const ConfirmClaimScreen({
    super.key,
    required this.ocr,
    this.localPath,
    this.runOcr = false,
  });

  final OcrResult ocr;
  final String? localPath;
  final bool runOcr;

  @override
  ConsumerState<ConfirmClaimScreen> createState() => _ConfirmClaimScreenState();
}

class _ConfirmClaimScreenState extends ConsumerState<ConfirmClaimScreen> {
  late OcrResult _ocr;
  late final TextEditingController _vendor;
  late final TextEditingController _amount;
  late final TextEditingController _vat;
  late final TextEditingController _total;
  late final TextEditingController _date;
  late final TextEditingController _remarks;
  int? _categoryId;
  int? _projectId;
  String _type = 'reimbursement';
  String _ocrMode = 'auto';
  String? _currency;
  bool _busy = false;
  String? _error;
  List<CategoryRef> _categories = const [];
  List<ProjectRef> _projects = const [];

  bool _analyzing = false;
  bool _ocrFailed = false;
  int _progress = 0;
  Timer? _ticker;

  @override
  void initState() {
    super.initState();
    _ocr = widget.ocr;
    _vendor = TextEditingController(text: _ocr.vendor);
    _amount = TextEditingController(text: _money(_ocr.amount));
    _vat = TextEditingController(text: _money(_ocr.vatAmount));
    _total = TextEditingController(text: _money(_ocr.totalAmount));
    _date = TextEditingController(text: _ocr.date);
    _remarks = TextEditingController();
    _currency = _normalizeCurrency(_ocr.currency);
    _loadReferenceData();
    if (widget.runOcr || _ocr.isPending) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _analyzeWithRetries());
    }
  }

  String _money(double? value) => value == null ? '' : value.toStringAsFixed(2);

  // Anything not recognized as AED/SAR is left unselected, never silently defaulted to AED — the employee must actively pick a currency.
  String? _normalizeCurrency(String? value) => (value == 'AED' || value == 'SAR') ? value : null;

  Future<void> _loadReferenceData() async {
    try {
      final api = ref.read(apiClientProvider);
      final categories = await api.categories();
      final projects = await api.projects();
      if (mounted) {
        setState(() {
          _categories = categories;
          _projects = projects;
          _categoryId ??= _matchExpenseType(categories) ?? (categories.isNotEmpty ? categories.first.id : null);
        });
      }
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

    Object? lastError;
    for (var i = 1; i <= maxAttempts; i++) {
      if (!mounted) return;
      if (i > 1) {
        setState(() => _progress = 20);
      }
      try {
        final result = await ref.read(apiClientProvider).analyzeReceipt(_ocr.receiptId, ocrMode: _ocrMode);
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
      _error = lastError?.toString();
    });
  }

  void _applyOcr(OcrResult result) {
    _ocr = result;
    _vendor.text = result.vendor;
    _amount.text = _money(result.amount);
    _vat.text = _money(result.vatAmount);
    _total.text = _money(result.totalAmount);
    _date.text = result.date;
    _currency = _normalizeCurrency(result.currency);
    final matched = _matchExpenseType(_categories, result.expenseType);
    if (matched != null) _categoryId = matched;
  }

  @override
  void dispose() {
    _ticker?.cancel();
    _vendor.dispose();
    _amount.dispose();
    _vat.dispose();
    _total.dispose();
    _date.dispose();
    _remarks.dispose();
    super.dispose();
  }

  Future<void> _submit({required bool asDraft}) async {
    if (_analyzing) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final amount = double.tryParse(_amount.text.trim());
      if (amount == null) {
        throw Exception('Enter a valid amount');
      }
      // A blank VAT field means "no VAT" (the backend reports a confident 0, not blank) — only a non-empty but unparseable value is an error.
      final vatText = _vat.text.trim();
      final vat = vatText.isEmpty ? 0.0 : double.tryParse(vatText);
      if (vat == null) {
        throw Exception('Enter a valid VAT amount');
      }
      final total = double.tryParse(_total.text.trim());
      if (total == null) {
        throw Exception('Enter a valid total amount');
      }
      if (_currency == null) {
        throw Exception('Select a currency (AED or SAR)');
      }
      if (_categoryId == null) {
        throw Exception('Select a category / expense type');
      }
      if (_date.text.trim().isEmpty) {
        throw Exception('Enter the bill date');
      }
      final selectedProject =
          _projectId == null ? null : _projects.firstWhere((p) => p.id == _projectId);
      final api = ref.read(apiClientProvider);
      final claim = await api.createClaim({
        'vendor': _vendor.text.trim(),
        'amount': amount,
        'vat_amount': vat,
        'total_amount': total,
        'currency': _currency,
        'bill_date': _date.text.trim(),
        'category_id': _categoryId,
        // TODO(region picker): hardcoded until a real per-bill region picker exists (Phase 6).
        'region_code': 'UAE',
        'type': _type,
        'project_id': _projectId,
        'op_number': selectedProject?.opNumber,
        'remarks': _remarks.text.trim().isEmpty ? null : _remarks.text.trim(),
        'receipt_id': _ocr.receiptId,
        's3_key': _ocr.s3Key,
        'submit': !asDraft,
      });
      if (!mounted) return;
      if (claim.duplicateWarning != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(claim.duplicateWarning!.message)),
        );
      }
      context.go('/claim/${claim.id}');
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final currency = _currency;
    final fieldsLocked = _analyzing;

    return Scaffold(
      appBar: const BrandAppBar(
        title: 'Confirm claim',
        automaticallyImplyLeading: true,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          if (widget.localPath != null)
            GestureDetector(
              onTap: () => _openImagePreview(context, widget.localPath!),
              child: Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.orange, width: 2),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(14),
                  child: Image.file(
                    File(widget.localPath!),
                    height: 200,
                    width: double.infinity,
                    fit: BoxFit.cover,
                  ),
                ),
              ),
            ),
          const SizedBox(height: 12),
          _OcrModeSelector(
            value: _ocrMode,
            enabled: !_analyzing,
            onChanged: (mode) {
              setState(() => _ocrMode = mode);
              _analyzeWithRetries();
            },
          ),
          if (_analyzing) ...[
            const SizedBox(height: 12),
            _OcrProgress(progress: _progress),
          ],
          if (_ocrFailed) ...[
            const SizedBox(height: 12),
            _ManualEntryBanner(
              onRetry: _analyzing ? null : () => _analyzeWithRetries(maxAttempts: 1),
            ),
          ],
          if (_ocr.duplicateWarning != null) ...[
            const SizedBox(height: 12),
            _notice(_ocr.duplicateWarning!.message),
          ],
          // Only shown once amount, VAT, and total are ALL present — a field that wasn't extracted isn't a real mismatch, it's missing data.
          if (_ocr.reconciliationMismatch &&
              _ocr.amount != null &&
              _ocr.vatAmount != null &&
              _ocr.totalAmount != null) ...[
            const SizedBox(height: 12),
            _notice("Amount + VAT doesn't match the total on this bill — please double-check these figures before submitting."),
          ],
          const SizedBox(height: 16),
          if (!_analyzing)
            const Padding(
              padding: EdgeInsets.only(bottom: 16),
              child: Text('Review every field before submitting. You can edit every value.'),
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
                    confidence: _ocrFailed ? null : _ocr.confidenceFor('vendor'),
                    allowArabic: true,
                  ),
                  const SizedBox(height: 12),
                  _CurrencyToggle(
                    value: _currency,
                    onChanged: (v) => setState(() => _currency = v),
                  ),
                  const SizedBox(height: 12),
                  _OcrTextField(
                    controller: _amount,
                    label: currency == null ? 'Amount (excl. VAT) *' : 'Amount excl. VAT ($currency) *',
                    lowConfidence: !_ocrFailed && _ocr.isLow('amount'),
                    confidence: _ocrFailed ? null : _ocr.confidenceFor('amount'),
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalInputFormatters,
                  ),
                  const SizedBox(height: 12),
                  _OcrTextField(
                    controller: _vat,
                    label: 'VAT amount (leave blank if none)',
                    lowConfidence: !_ocrFailed && _ocr.isLow('vat_amount'),
                    confidence: _ocrFailed ? null : _ocr.confidenceFor('vat_amount'),
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalInputFormatters,
                  ),
                  const SizedBox(height: 12),
                  _OcrTextField(
                    controller: _total,
                    label: currency == null ? 'Total amount *' : 'Total amount ($currency) *',
                    lowConfidence: !_ocrFailed && _ocr.isLow('total_amount'),
                    confidence: _ocrFailed ? null : _ocr.confidenceFor('total_amount'),
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalInputFormatters,
                  ),
                  const SizedBox(height: 12),
                  _OcrTextField(
                    controller: _date,
                    label: 'Bill date *',
                    lowConfidence: !_ocrFailed && _ocr.isLow('date'),
                    confidence: _ocrFailed ? null : _ocr.confidenceFor('date'),
                  ),
                  const SizedBox(height: 12),
                  _flaggedDecorator(
                    label: 'Expense type *',
                    low: !_ocrFailed && _ocr.isLow('expense_type'),
                    confidence: _ocrFailed ? null : _ocr.confidenceFor('expense_type'),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<int>(
                        isExpanded: true,
                        value: _categoryId,
                        items: _categories
                            .map((c) => DropdownMenuItem(value: c.id, child: Text(c.name)))
                            .toList(),
                        onChanged: (v) => setState(() => _categoryId = v),
                      ),
                    ),
                  ),
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
                  DropdownMenuItem(value: 'reimbursement', child: Text('Reimbursement')),
                  DropdownMenuItem(value: 'petty_cash', child: Text('Petty cash')),
                ],
                onChanged: (v) => setState(() => _type = v ?? 'reimbursement'),
              ),
            ),
          ),
          const SizedBox(height: 12),
          InputDecorator(
            decoration: const InputDecoration(labelText: 'Project / OP'),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<int?>(
                isExpanded: true,
                value: _projectId,
                items: [
                  const DropdownMenuItem(value: null, child: Text('None')),
                  ..._projects.map((p) => DropdownMenuItem(value: p.id, child: Text(p.name))),
                ],
                onChanged: (v) => setState(() => _projectId = v),
              ),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _remarks,
            maxLines: 2,
            decoration: const InputDecoration(labelText: 'Remarks (optional)'),
          ),
          if (_error != null && !_ocrFailed) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          const SizedBox(height: 20),
          FilledButton(
            onPressed: (_busy || _analyzing) ? null : () => _submit(asDraft: false),
            child: Text(_busy ? 'Submitting…' : _analyzing ? 'Waiting for bill reading…' : 'Submit for approval'),
          ),
          const SizedBox(height: 10),
          OutlinedButton(
            onPressed: (_busy || _analyzing) ? null : () => _submit(asDraft: true),
            child: const Text('Save as draft'),
          ),
        ],
      ),
    );
  }

  void _openImagePreview(BuildContext context, String localPath) {
    openImagePreview(context, Image.file(File(localPath)));
  }

  Widget _notice(String text) {
    return Material(
      color: AppColors.warningSoft,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Text(text),
      ),
    );
  }
}

class _OcrProgress extends StatelessWidget {
  const _OcrProgress({required this.progress});

  final int progress;

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
                style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.darkBlue),
              ),
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
  const _ManualEntryBanner({this.onRetry});

  final VoidCallback? onRetry;

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
            const Expanded(
              child: Text(
                'Couldn’t read this bill. Enter the details below.',
                style: TextStyle(fontWeight: FontWeight.w600, height: 1.3),
              ),
            ),
            if (onRetry != null) ...[
              const SizedBox(width: 8),
              OutlinedButton(
                onPressed: onRetry,
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.darkBlue,
                  side: const BorderSide(color: AppColors.darkBlue),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  minimumSize: Size.zero,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  visualDensity: VisualDensity.compact,
                ),
                child: const Text('Recheck once more', style: TextStyle(fontSize: 12)),
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
      borderSide: BorderSide(color: low ? AppColors.orange : AppColors.divider, width: low ? 1.6 : 1),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: BorderSide(color: low ? AppColors.orange : AppColors.darkBlue, width: 1.5),
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
  });

  final TextEditingController controller;
  final String label;
  final bool lowConfidence;
  final double? confidence;
  final TextInputType? keyboardType;
  final bool allowArabic;
  final List<TextInputFormatter>? inputFormatters;

  @override
  State<_OcrTextField> createState() => _OcrTextFieldState();
}

class _OcrTextFieldState extends State<_OcrTextField> {
  @override
  Widget build(BuildContext context) {
    final arabic = widget.allowArabic && _arabic.hasMatch(widget.controller.text);
    return TextField(
      controller: widget.controller,
      keyboardType: widget.keyboardType ?? TextInputType.text,
      textCapitalization: widget.allowArabic ? TextCapitalization.sentences : TextCapitalization.none,
      textDirection: arabic ? TextDirection.rtl : TextDirection.ltr,
      inputFormatters: widget.inputFormatters,
      onChanged: widget.allowArabic ? (_) => setState(() {}) : null,
      decoration: _ocrDecoration(
        label: widget.label,
        low: widget.lowConfidence,
        confidence: widget.confidence,
      ),
    );
  }
}

class _OcrModeSelector extends StatelessWidget {
  const _OcrModeSelector({required this.value, required this.enabled, required this.onChanged});

  final String value; // 'auto' | 'en' | 'ar'
  final bool enabled;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(bottom: 4),
            child: Text('Bill language', style: TextStyle(fontSize: 12, color: AppColors.darkBlue)),
          ),
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'auto', label: Text('Auto')),
              ButtonSegment(value: 'en', label: Text('English')),
              ButtonSegment(value: 'ar', label: Text('Arabic')),
            ],
            selected: {value},
            onSelectionChanged: enabled ? (selection) => onChanged(selection.first) : null,
          ),
        ],
      ),
    );
  }
}

class _CurrencyToggle extends StatelessWidget {
  const _CurrencyToggle({required this.value, required this.onChanged});

  // null = no currency selected yet — the employee must tap AED or SAR before submitting (see the required-field check in _submit()).
  final String? value;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'AED', label: Text('AED')),
              ButtonSegment(value: 'SAR', label: Text('SAR')),
            ],
            selected: value == null ? const <String>{} : {value!},
            emptySelectionAllowed: true,
            onSelectionChanged: (selection) => onChanged(selection.first),
          ),
          if (value == null)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                'Currency not detected — select AED or SAR *',
                style: TextStyle(color: AppColors.orange, fontSize: 12),
              ),
            ),
        ],
      ),
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


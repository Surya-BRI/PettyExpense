import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';

import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../widgets/op_code_field.dart';

final _amountFormatters = <TextInputFormatter>[
  FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d{0,2}')),
];
final _qtyFormatters = <TextInputFormatter>[
  FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d{0,3}')),
];

String _fmt(double? v, {int digits = 2}) {
  if (v == null) return '';
  // Whole quantities read better as "5" than "5.000".
  if (digits > 2 && v == v.roundToDouble()) return v.toStringAsFixed(0);
  return v.toStringAsFixed(digits);
}

/// One editable item line on a "Multiple items" bill. Owns its text controllers --
/// call [dispose] when the line is removed or the screen goes away.
class LineItemDraft {
  LineItemDraft({
    String description = '',
    double? quantity,
    double? amount,
    this.categoryId,
    this.opResult,
  }) : description = TextEditingController(text: description),
       quantity = TextEditingController(text: _fmt(quantity, digits: 3)),
       amount = TextEditingController(text: _fmt(amount));

  factory LineItemDraft.fromOcr(OcrLineItem item, {int? categoryId}) =>
      LineItemDraft(
        description: item.description,
        quantity: item.quantity,
        amount: item.amount,
        categoryId: categoryId,
      );

  final TextEditingController description;
  final TextEditingController quantity;
  final TextEditingController amount;
  int? categoryId;
  // The project/OP this item is allocated to -- null means "use the claim-level OP".
  // Kept as the resolved search result (not just the code) so a new line can copy it
  // straight into its own OpCodeField without re-hitting the search API.
  OpportunityResult? opResult;

  double? get amountValue => double.tryParse(amount.text.trim());
  double? get quantityValue => quantity.text.trim().isEmpty
      ? null
      : double.tryParse(quantity.text.trim());

  /// A real counted quantity (pieces, boxes, units) is almost always a whole number --
  /// a fractional one ("16.01", "151.062") is a strong tell that OCR actually read a
  /// Rate/VAT% column into this field instead of the real Qty column, a bug this app has
  /// hit repeatedly on dense multi-column invoices. Non-blocking: just a nudge to double
  /// check, since genuinely fractional quantities (metres, kilos) do exist.
  bool get quantityLooksOff {
    final q = quantityValue;
    return q != null && q != q.roundToDouble();
  }

  /// Why this line can't be submitted yet, or null if it's complete.
  String? get problem {
    if (description.text.trim().isEmpty) return 'Add the item name';
    if (amountValue == null) return 'Add the amount';
    if (categoryId == null) return 'Pick a category';
    return null;
  }

  Map<String, dynamic> toJson() => {
    'description': description.text.trim(),
    'quantity': quantityValue,
    'amount': amountValue,
    'category_id': categoryId,
    'op_number': opResult?.opCode,
  };

  void dispose() {
    description.dispose();
    quantity.dispose();
    amount.dispose();
  }
}

/// Editable list of item lines: name, quantity, amount and category per line, plus
/// add / remove. The parent owns the drafts and recomputes totals in [onChanged].
/// Shows one item card at a time with Previous/Next navigation -- a bill with a
/// dozen-plus items (common on pharmacy/hardware receipts) made a stacked list of
/// cards an unreasonably long scroll.
class LineItemsEditor extends StatefulWidget {
  const LineItemsEditor({
    super.key,
    required this.lines,
    required this.categories,
    required this.currency,
    required this.onChanged,
    required this.onAdd,
    required this.onRemove,
    this.showProblems = false,
  });

  final List<LineItemDraft> lines;
  final List<CategoryRef> categories;
  final String? currency;
  final VoidCallback onChanged;
  final VoidCallback onAdd;
  final ValueChanged<int> onRemove;

  /// After a failed submit, highlight what each incomplete line is missing.
  final bool showProblems;

  @override
  State<LineItemsEditor> createState() => _LineItemsEditorState();
}

class _LineItemsEditorState extends State<LineItemsEditor> {
  int _index = 0;

  void _goTo(int i) =>
      setState(() => _index = i.clamp(0, widget.lines.length - 1));

  @override
  Widget build(BuildContext context) {
    final lines = widget.lines;
    final index = _index.clamp(0, lines.length - 1);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            IconButton(
              tooltip: 'Previous item',
              visualDensity: VisualDensity.compact,
              onPressed: index > 0 ? () => _goTo(index - 1) : null,
              icon: Icon(PhosphorIcons.caretLeft()),
            ),
            Expanded(
              child: Center(
                child: Text(
                  'Item ${index + 1} of ${lines.length}',
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    color: AppColors.darkBlue,
                  ),
                ),
              ),
            ),
            IconButton(
              tooltip: 'Next item',
              visualDensity: VisualDensity.compact,
              onPressed: index < lines.length - 1
                  ? () => _goTo(index + 1)
                  : null,
              icon: Icon(PhosphorIcons.caretRight()),
            ),
          ],
        ),
        _LineCard(
          key: ObjectKey(lines[index]),
          index: index,
          line: lines[index],
          categories: widget.categories,
          currency: widget.currency,
          canRemove: lines.length > 1,
          showProblem: widget.showProblems,
          onChanged: widget.onChanged,
          onRemove: () {
            widget.onRemove(index);
            // `lines` is the same List instance the parent mutates in place, so its
            // length already reflects the removal here -- land on the item that
            // slid into this slot, or step back if the last item was removed.
            if (lines.isNotEmpty) _goTo(index);
          },
        ),
        const SizedBox(height: 10),
        OutlinedButton.icon(
          onPressed: () {
            widget.onAdd();
            // Same in-place-mutation reasoning as above: lines.length already
            // includes the new line by the time onAdd() returns.
            _goTo(lines.length - 1);
          },
          icon: Icon(PhosphorIcons.plus()),
          label: const Text('Add item'),
        ),
      ],
    );
  }
}

class _LineCard extends StatelessWidget {
  const _LineCard({
    super.key,
    required this.index,
    required this.line,
    required this.categories,
    required this.currency,
    required this.canRemove,
    required this.showProblem,
    required this.onChanged,
    required this.onRemove,
  });

  final int index;
  final LineItemDraft line;
  final List<CategoryRef> categories;
  final String? currency;
  final bool canRemove;
  final bool showProblem;
  final VoidCallback onChanged;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    final problem = showProblem ? line.problem : null;
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 4, 12),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: problem != null ? AppColors.orange : AppColors.divider,
          width: problem != null ? 1.6 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Text(
                'Item ${index + 1}',
                style: const TextStyle(
                  fontWeight: FontWeight.w700,
                  color: AppColors.darkBlue,
                ),
              ),
              if (problem != null) ...[
                const SizedBox(width: 8),
                Flexible(
                  child: Text(
                    problem,
                    style: const TextStyle(
                      color: AppColors.orange,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
              const Spacer(),
              IconButton(
                tooltip: 'Remove item',
                visualDensity: VisualDensity.compact,
                onPressed: canRemove ? onRemove : null,
                icon: Icon(PhosphorIcons.trash()),
              ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextField(
                  controller: line.description,
                  textCapitalization: TextCapitalization.sentences,
                  decoration: const InputDecoration(
                    labelText: 'Item *',
                    isDense: true,
                  ),
                  onChanged: (_) => onChanged(),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: TextField(
                        controller: line.quantity,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        inputFormatters: _qtyFormatters,
                        decoration: InputDecoration(
                          labelText: 'Qty',
                          isDense: true,
                          filled: line.quantityLooksOff,
                          fillColor: AppColors.warningSoft,
                          enabledBorder: line.quantityLooksOff
                              ? OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(4),
                                  borderSide: const BorderSide(
                                    color: AppColors.orange,
                                    width: 1.6,
                                  ),
                                )
                              : null,
                        ),
                        onChanged: (_) => onChanged(),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      flex: 3,
                      child: TextField(
                        controller: line.amount,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        inputFormatters: _amountFormatters,
                        decoration: InputDecoration(
                          labelText: currency == null
                              ? 'Amount *'
                              : 'Amount ($currency) *',
                          isDense: true,
                        ),
                        onChanged: (_) => onChanged(),
                      ),
                    ),
                  ],
                ),
                if (line.quantityLooksOff) ...[
                  const SizedBox(height: 4),
                  const Text(
                    'This quantity looks unusual -- double-check it against the bill.',
                    style: TextStyle(color: AppColors.orange, fontSize: 11.5),
                  ),
                ],
                const SizedBox(height: 10),
                InputDecorator(
                  decoration: const InputDecoration(
                    labelText: 'Category *',
                    isDense: true,
                  ),
                  child: DropdownButtonHideUnderline(
                    child: DropdownButton<int>(
                      isExpanded: true,
                      isDense: true,
                      value: categories.any((c) => c.id == line.categoryId)
                          ? line.categoryId
                          : null,
                      hint: const Text('Choose'),
                      items: [
                        for (final c in categories)
                          DropdownMenuItem(value: c.id, child: Text(c.name)),
                      ],
                      onChanged: (v) {
                        line.categoryId = v;
                        onChanged();
                      },
                    ),
                  ),
                ),
                const SizedBox(height: 10),
                OpCodeField(
                  key: ValueKey(line),
                  label: 'Project / OP code (optional)',
                  dense: true,
                  initial: line.opResult,
                  onResolved: (v) {
                    line.opResult = v;
                    onChanged();
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

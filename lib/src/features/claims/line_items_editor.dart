import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../api/models.dart';
import '../../theme/app_theme.dart';

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

  double? get amountValue => double.tryParse(amount.text.trim());
  double? get quantityValue => quantity.text.trim().isEmpty
      ? null
      : double.tryParse(quantity.text.trim());

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
  };

  void dispose() {
    description.dispose();
    quantity.dispose();
    amount.dispose();
  }
}

/// Editable list of item lines: name, quantity, amount and category per line, plus
/// add / remove. The parent owns the drafts and recomputes totals in [onChanged].
class LineItemsEditor extends StatelessWidget {
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
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (var i = 0; i < lines.length; i++) ...[
          _LineCard(
            key: ObjectKey(lines[i]),
            index: i,
            line: lines[i],
            categories: categories,
            currency: currency,
            canRemove: lines.length > 1,
            showProblem: showProblems,
            onChanged: onChanged,
            onRemove: () => onRemove(i),
          ),
          const SizedBox(height: 10),
        ],
        OutlinedButton.icon(
          onPressed: onAdd,
          icon: const Icon(Icons.add),
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
                icon: const Icon(Icons.delete_outline),
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
                        decoration: const InputDecoration(
                          labelText: 'Qty',
                          isDense: true,
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
              ],
            ),
          ),
        ],
      ),
    );
  }
}

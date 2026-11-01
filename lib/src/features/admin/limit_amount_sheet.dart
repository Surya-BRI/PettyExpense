import 'package:flutter/material.dart';

import '../../theme/app_theme.dart';

class LimitAmountSheet extends StatefulWidget {
  const LimitAmountSheet({
    super.key,
    required this.title,
    required this.confirmLabel,
    required this.currency,
    this.initial,
  });

  final String title;
  final String confirmLabel;
  final String currency;
  final double? initial;

  @override
  State<LimitAmountSheet> createState() => _LimitAmountSheetState();
}

class _LimitAmountSheetState extends State<LimitAmountSheet> {
  late final TextEditingController _controller;
  String? _error;

  @override
  void initState() {
    super.initState();
    final initial = widget.initial;
    _controller = TextEditingController(
      text: initial == null ? '' : (initial == initial.roundToDouble() ? '${initial.round()}' : '$initial'),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 16, 20, 20 + MediaQuery.viewInsetsOf(context).bottom),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(widget.title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
          const SizedBox(height: 12),
          TextField(
            controller: _controller,
            autofocus: true,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: InputDecoration(
              labelText: 'Amount (${widget.currency})',
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          const SizedBox(height: 16),
          FilledButton(
            onPressed: () {
              final parsed = double.tryParse(_controller.text.trim());
              if (parsed == null || parsed < 0) {
                setState(() => _error = 'Enter a valid amount');
                return;
              }
              Navigator.of(context).pop(parsed);
            },
            child: Text(widget.confirmLabel),
          ),
        ],
      ),
    );
  }
}

Future<double?> askLimitAmount({
  required BuildContext context,
  required String title,
  required String confirmLabel,
  required String currency,
  double? initial,
}) {
  return showModalBottomSheet<double>(
    context: context,
    isScrollControlled: true,
    backgroundColor: AppColors.card,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (ctx) => LimitAmountSheet(
      title: title,
      confirmLabel: confirmLabel,
      currency: currency,
      initial: initial,
    ),
  );
}

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';

import '../api/api_client.dart';
import '../api/models.dart';
import '../theme/app_theme.dart';

/// Debounced "Project / OP code" search-as-you-type field, backed by
/// GET /api/opportunities/search. Used claim-wide in ConfirmClaimScreen and
/// per-line in LineItemsEditor -- lives here so both share one implementation.
class OpCodeField extends ConsumerStatefulWidget {
  const OpCodeField({
    super.key,
    required this.label,
    this.initial,
    this.dense = false,
    required this.onResolved,
  });

  final String label;
  final OpportunityResult? initial;
  final bool dense;
  final ValueChanged<OpportunityResult?> onResolved;

  @override
  ConsumerState<OpCodeField> createState() => _OpCodeFieldState();
}

class _OpCodeFieldState extends ConsumerState<OpCodeField> {
  late final TextEditingController _ctrl = TextEditingController(text: widget.initial?.opCode ?? '');
  late OpportunityResult? _resolved = widget.initial;
  bool _searching = false;
  String? _error;
  Timer? _debounce;

  @override
  void dispose() {
    _debounce?.cancel();
    _ctrl.dispose();
    super.dispose();
  }

  void _search(String val) {
    _debounce?.cancel();
    if (val.trim().isEmpty) {
      setState(() {
        _resolved = null;
        _error = null;
      });
      widget.onResolved(null);
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 600), () async {
      setState(() {
        _searching = true;
        _error = null;
      });
      try {
        final result = await ref.read(apiClientProvider).searchOpportunity(val.trim());
        if (mounted) {
          setState(() {
            _resolved = result;
            _error = result == null ? 'OP code not found' : null;
          });
          widget.onResolved(result);
        }
      } catch (_) {
        if (mounted) setState(() => _error = 'Search failed');
      } finally {
        if (mounted) setState(() => _searching = false);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: _ctrl,
          decoration: InputDecoration(
            labelText: widget.label,
            hintText: 'e.g. OP-2201',
            isDense: widget.dense,
            suffixIcon: _searching
                ? const Padding(
                    padding: EdgeInsets.all(12),
                    child: SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
                  )
                : _resolved != null
                    ? IconButton(
                        icon: Icon(PhosphorIcons.x(), size: 18),
                        onPressed: () {
                          _ctrl.clear();
                          setState(() {
                            _resolved = null;
                            _error = null;
                          });
                          widget.onResolved(null);
                        },
                      )
                    : null,
            errorText: _error,
          ),
          onChanged: _search,
        ),
        if (_resolved != null) ...[
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: AppColors.successSoft,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_resolved!.name, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                if (_resolved!.buCode != null || _resolved!.salesPerson != null)
                  Text(
                    [_resolved!.buCode, _resolved!.salesPerson].whereType<String>().join(' · '),
                    style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                  ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

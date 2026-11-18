import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../theme/app_theme.dart';

final regionSlaProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, int>((ref, regionId) {
  return ref.watch(apiClientProvider).regionSla(regionId);
});

/// "24 hrs", "1 hr 30 min", "15 min" for a time limit given in hours (always hours, never days).
String formatSlaHours(double hours) {
  final totalMinutes = (hours * 60).round();
  final h = totalMinutes ~/ 60;
  final m = totalMinutes % 60;
  final parts = <String>[
    if (h > 0) '$h hr${h == 1 ? '' : 's'}',
    if (m > 0) '$m min',
  ];
  return parts.isEmpty ? '0 min' : parts.join(' ');
}

/// Approvers tab: a plain "SLA time" button; the time limits are set in a sheet it opens.
class SlaTimeButton extends StatelessWidget {
  const SlaTimeButton({super.key, required this.regionId});

  final int regionId;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: () => showSlaTimeSheet(context, regionId),
        style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
        icon: Icon(PhosphorIcons.timer(), size: 18),
        label: const Text('SLA time'),
      ),
    );
  }
}

Future<void> showSlaTimeSheet(BuildContext context, int regionId) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    backgroundColor: AppColors.card,
    builder: (sheetContext) => Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(sheetContext).viewInsets.bottom),
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(4, 0, 4, 16),
        child: ApprovalTimeLimitsCard(regionId: regionId, inSheet: true),
      ),
    ),
  );
}

/// Admin: how long each approval step has before the approver is warned (and, one more full
/// limit later, the next step + Admin are told). [inSheet]: opened from the "SLA time" button --
/// starts straight in edit mode and closes the sheet on Save / Cancel.
class ApprovalTimeLimitsCard extends ConsumerStatefulWidget {
  const ApprovalTimeLimitsCard({super.key, required this.regionId, this.inSheet = false});

  final int regionId;
  final bool inSheet;

  @override
  ConsumerState<ApprovalTimeLimitsCard> createState() => _ApprovalTimeLimitsCardState();
}

class _StageFields {
  _StageFields(this.stage, this.label, double hours)
      : hours = TextEditingController(text: '${(hours * 60).round() ~/ 60}'),
        minutes = TextEditingController(text: '${(hours * 60).round() % 60}');

  final String stage;
  final String label;
  final TextEditingController hours;
  final TextEditingController minutes;

  /// Null when empty or not a number.
  double? get value {
    final h = int.tryParse(hours.text.trim().isEmpty ? '0' : hours.text.trim());
    final m = int.tryParse(minutes.text.trim().isEmpty ? '0' : minutes.text.trim());
    if (h == null || m == null) return null;
    return h + m / 60.0;
  }

  void dispose() {
    hours.dispose();
    minutes.dispose();
  }
}

class _ApprovalTimeLimitsCardState extends ConsumerState<ApprovalTimeLimitsCard> {
  List<_StageFields>? _fields;
  bool _editing = false;
  bool _saving = false;
  String? _error;

  @override
  void dispose() {
    for (final f in _fields ?? const <_StageFields>[]) {
      f.dispose();
    }
    super.dispose();
  }

  void _fillFields(Map<String, dynamic> data) {
    for (final f in _fields ?? const <_StageFields>[]) {
      f.dispose();
    }
    _fields = [
      for (final s in (data['stages'] as List? ?? const []))
        _StageFields(
          (s as Map)['stage'] as String,
          s['label'] as String? ?? s['stage'] as String,
          (s['hours'] as num).toDouble(),
        ),
    ];
    _editing = true;
    _error = null;
  }

  void _startEditing(Map<String, dynamic> data) => setState(() => _fillFields(data));

  void _cancel() {
    if (widget.inSheet) {
      Navigator.of(context).pop();
    } else {
      setState(() => _editing = false);
    }
  }

  Future<void> _save(Map<String, dynamic> data) async {
    final minHours = (data['min_hours'] as num?)?.toDouble() ?? 5 / 60;
    final maxHours = (data['max_hours'] as num?)?.toDouble() ?? 720;
    final values = <String, double>{};
    for (final f in _fields!) {
      final v = f.value;
      if (v == null || v < minHours - 1e-9 || v > maxHours) {
        setState(() => _error = '${f.label}: enter between 5 minutes and 720 hours');
        return;
      }
      values[f.stage] = v;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).updateRegionSla(widget.regionId, values);
      ref.invalidate(regionSlaProvider(widget.regionId));
      if (!mounted) return;
      final messenger = ScaffoldMessenger.of(context);
      if (widget.inSheet) {
        Navigator.of(context).pop();
      } else {
        setState(() {
          _saving = false;
          _editing = false;
        });
      }
      messenger.showSnackBar(const SnackBar(content: Text('SLA time saved')));
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = '$e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(regionSlaProvider(widget.regionId));
    // Opened from the button: go straight to the hours / minutes fields.
    if (widget.inSheet && _fields == null && async.hasValue) {
      _fillFields(async.requireValue);
    }
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      decoration: widget.inSheet
          ? null
          : BoxDecoration(
              color: AppColors.card,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.divider),
            ),
      child: async.when(
        loading: () => const Padding(
          padding: EdgeInsets.all(12),
          child: Center(child: CircularProgressIndicator()),
        ),
        error: (e, _) => Text('Could not load SLA time: $e'),
        data: (data) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Icon(PhosphorIcons.timer(), color: AppColors.darkBlue, size: 20),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'SLA time',
                    style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15),
                  ),
                ),
                if (!_editing)
                  TextButton.icon(
                    onPressed: () => _startEditing(data),
                    icon: Icon(PhosphorIcons.pencilSimple(), size: 16),
                    label: const Text('Edit'),
                  ),
              ],
            ),
            const SizedBox(height: 4),
            const Text(
              'If an approver does not act in time they get an overdue alert. '
              'One more full time limit later, the next step and Admin are alerted.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 12.5, height: 1.35),
            ),
            const SizedBox(height: 10),
            if (_editing) ..._editRows() else ..._viewRows(data),
            if (_error != null) ...[
              const SizedBox(height: 8),
              Text(_error!, style: const TextStyle(color: AppColors.danger, fontSize: 13)),
            ],
            if (_editing) ...[
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: _saving ? null : _cancel,
                    child: const Text('Cancel'),
                  ),
                  const SizedBox(width: 8),
                  FilledButton(
                    onPressed: _saving ? null : () => _save(data),
                    child: _saving
                        ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Text('Save'),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  List<Widget> _viewRows(Map<String, dynamic> data) => [
        for (final s in (data['stages'] as List? ?? const []))
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 5),
            child: Row(
              children: [
                Expanded(child: Text((s as Map)['label'] as String? ?? s['stage'] as String)),
                Text(
                  formatSlaHours((s['hours'] as num).toDouble()),
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ],
            ),
          ),
      ];

  List<Widget> _editRows() => [
        for (final f in _fields!)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 5),
            child: Row(
              children: [
                Expanded(child: Text(f.label)),
                _NumberBox(controller: f.hours, suffix: 'h', fieldKey: Key('sla_${f.stage}_hours')),
                const SizedBox(width: 8),
                _NumberBox(controller: f.minutes, suffix: 'min', fieldKey: Key('sla_${f.stage}_minutes')),
              ],
            ),
          ),
      ];
}

class _NumberBox extends StatelessWidget {
  const _NumberBox({required this.controller, required this.suffix, required this.fieldKey});

  final TextEditingController controller;
  final String suffix;
  final Key fieldKey;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 84,
      child: TextField(
        key: fieldKey,
        controller: controller,
        keyboardType: TextInputType.number,
        inputFormatters: [FilteringTextInputFormatter.digitsOnly],
        textAlign: TextAlign.end,
        decoration: InputDecoration(
          isDense: true,
          suffixText: suffix,
          contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
          border: const OutlineInputBorder(),
        ),
      ),
    );
  }
}

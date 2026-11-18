import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../theme/app_theme.dart';
import '../../widgets/app_nav_drawer.dart';
import '../../widgets/brand_app_bar.dart';

/// "18 Nov 2026" from "2026-11-18".
String formatBackupDate(String iso) {
  final d = DateTime.tryParse(iso);
  return d == null ? iso : DateFormat('d MMM yyyy').format(d);
}

String _iso(DateTime d) => DateFormat('yyyy-MM-dd').format(d);

String _personLine(Map p) {
  final role = (p['role_label'] as String? ?? '').trim();
  final dept = (p['department_name'] as String? ?? '').trim();
  return [
    p['display_name'] as String? ?? '',
    if (role.isNotEmpty) role,
    if (dept.isNotEmpty && role == 'Head of Department') dept,
  ].join(' · ');
}

/// Approver's own screen: who covers my bills while I'm away.
class MyBackupScreen extends ConsumerWidget {
  const MyBackupScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final api = ref.watch(apiClientProvider);
    return Scaffold(
      backgroundColor: AppColors.background,
      drawer: const AppNavDrawer(),
      appBar: const BrandAppBar(title: 'My backup'),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 28),
        children: [
          BackupApproverPanel(
            whose: 'your',
            load: api.myBackup,
            save: (backupId, start, end) => api.setMyBackup(backupId, start, end),
            remove: api.removeMyBackup,
          ),
        ],
      ),
    );
  }
}

/// Lists current / upcoming backups with Remove, and a form to set a new one. Used by the
/// approver ([MyBackupScreen]) and by Admin on a person's page.
class BackupApproverPanel extends StatefulWidget {
  const BackupApproverPanel({
    super.key,
    required this.whose,
    required this.load,
    required this.save,
    required this.remove,
  });

  /// "your" or "Rashid's" -- used in the help text.
  final String whose;
  final Future<Map<String, dynamic>> Function() load;
  final Future<void> Function(int backupId, String startDate, String endDate) save;
  final Future<void> Function(int delegationId) remove;

  @override
  State<BackupApproverPanel> createState() => _BackupApproverPanelState();
}

class _BackupApproverPanelState extends State<BackupApproverPanel> {
  Map<String, dynamic>? _data;
  String? _loadError;
  bool _editing = false;
  bool _busy = false;
  String? _error;
  int? _backupId;
  DateTime? _start;
  DateTime? _end;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<void> _reload() async {
    try {
      final data = await widget.load();
      if (!mounted) return;
      setState(() {
        _data = data;
        _loadError = null;
      });
    } catch (e) {
      if (mounted) setState(() => _loadError = '$e');
    }
  }

  DateTime get _today {
    final t = DateTime.tryParse(_data?['today'] as String? ?? '');
    final now = DateTime.now();
    return t ?? DateTime(now.year, now.month, now.day);
  }

  void _startEditing() => setState(() {
        _editing = true;
        _error = null;
        _backupId = null;
        _start = _today;
        _end = _today.add(const Duration(days: 1));
      });

  Future<void> _pickDate({required bool start}) async {
    final first = _today;
    final initial = (start ? _start : _end) ?? first;
    final picked = await showDatePicker(
      context: context,
      initialDate: initial.isBefore(first) ? first : initial,
      firstDate: first,
      lastDate: first.add(const Duration(days: 365)),
    );
    if (picked == null) return;
    setState(() {
      if (start) {
        _start = picked;
        if (_end != null && _end!.isBefore(picked)) _end = picked;
      } else {
        _end = picked;
      }
    });
  }

  Future<void> _save() async {
    if (_backupId == null) {
      setState(() => _error = 'Choose the backup approver');
      return;
    }
    if (_start == null || _end == null) {
      setState(() => _error = 'Choose the dates');
      return;
    }
    if (_end!.isBefore(_start!)) {
      setState(() => _error = 'The end date must be on or after the start date');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.save(_backupId!, _iso(_start!), _iso(_end!));
      if (!mounted) return;
      setState(() {
        _busy = false;
        _editing = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Backup approver saved')));
      await _reload();
    } catch (e) {
      if (mounted) {
        setState(() {
          _busy = false;
          _error = '$e';
        });
      }
    }
  }

  Future<void> _remove(Map b) async {
    final name = (b['backup'] as Map?)?['display_name'] ?? 'this backup';
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Remove backup?'),
        content: Text('Bills will go back to the usual approver instead of $name.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Remove')),
        ],
      ),
    );
    if (ok != true) return;
    setState(() => _busy = true);
    try {
      await widget.remove((b['id'] as num).toInt());
      await _reload();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.divider),
      ),
      child: _data == null
          ? Padding(
              padding: const EdgeInsets.all(12),
              child: Center(
                child: _loadError == null ? const CircularProgressIndicator() : Text(_loadError!),
              ),
            )
          : Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    Icon(PhosphorIcons.userSwitch(), color: AppColors.darkBlue, size: 20),
                    const SizedBox(width: 8),
                    const Expanded(
                      child: Text('Backup approver', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  'Between the dates, bills waiting for ${widget.whose} approval go to the backup instead. '
                  'They come back automatically when the dates end.',
                  style: const TextStyle(color: AppColors.textSecondary, fontSize: 12.5, height: 1.35),
                ),
                const SizedBox(height: 10),
                ..._backupRows(),
                if (_editing) ..._form() else ...[
                  const SizedBox(height: 6),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: _busy ? null : _startEditing,
                      style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
                      icon: Icon(PhosphorIcons.plus(), size: 18),
                      label: const Text('Set backup'),
                    ),
                  ),
                ],
              ],
            ),
    );
  }

  List<Widget> _backupRows() {
    final backups = (_data?['backups'] as List? ?? const []).cast<Map>();
    if (backups.isEmpty) {
      return const [
        Padding(
          padding: EdgeInsets.symmetric(vertical: 4),
          child: Text('No backup set.', style: TextStyle(color: AppColors.textSecondary)),
        ),
      ];
    }
    return [
      for (final b in backups)
        Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.fromLTRB(12, 10, 4, 10),
          decoration: BoxDecoration(
            color: AppColors.background,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _personLine(b['backup'] as Map? ?? const {}),
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 3),
                    Row(
                      children: [
                        Flexible(
                          child: Text(
                            '${formatBackupDate('${b['start_date']}')} – ${formatBackupDate('${b['end_date']}')}',
                            style: const TextStyle(color: AppColors.textSecondary, fontSize: 12.5),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          color: (b['is_active'] == true ? AppColors.success : AppColors.darkBlue).withValues(alpha: 0.12),
                          child: Text(
                            b['is_active'] == true ? 'Active now' : 'Upcoming',
                            style: TextStyle(
                              color: b['is_active'] == true ? AppColors.success : AppColors.darkBlue,
                              fontWeight: FontWeight.w700,
                              fontSize: 11,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              TextButton(
                onPressed: _busy ? null : () => _remove(b),
                child: const Text('Remove', style: TextStyle(color: AppColors.danger)),
              ),
            ],
          ),
        ),
    ];
  }

  List<Widget> _form() {
    final candidates = (_data?['candidates'] as List? ?? const []).cast<Map>();
    return [
      const SizedBox(height: 6),
      if (candidates.isEmpty)
        const Text(
          'No other approver in this company can be the backup.',
          style: TextStyle(color: AppColors.textSecondary),
        )
      else
        DropdownButtonFormField<int>(
          key: const Key('backup_person'),
          initialValue: _backupId,
          isExpanded: true,
          decoration: const InputDecoration(labelText: 'Backup approver', border: OutlineInputBorder()),
          items: [
            for (final c in candidates)
              DropdownMenuItem(
                value: (c['id'] as num).toInt(),
                child: Text(_personLine(c), overflow: TextOverflow.ellipsis),
              ),
          ],
          onChanged: _busy ? null : (v) => setState(() => _backupId = v),
        ),
      const SizedBox(height: 12),
      Row(
        children: [
          Expanded(child: _DateBox(label: 'From', value: _start, onTap: () => _pickDate(start: true))),
          const SizedBox(width: 10),
          Expanded(child: _DateBox(label: 'To', value: _end, onTap: () => _pickDate(start: false))),
        ],
      ),
      if (_error != null) ...[
        const SizedBox(height: 8),
        Text(_error!, style: const TextStyle(color: AppColors.danger, fontSize: 13)),
      ],
      const SizedBox(height: 12),
      Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          TextButton(
            onPressed: _busy ? null : () => setState(() => _editing = false),
            child: const Text('Cancel'),
          ),
          const SizedBox(width: 8),
          FilledButton(
            onPressed: _busy || candidates.isEmpty ? null : _save,
            child: _busy
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Save'),
          ),
        ],
      ),
    ];
  }
}

class _DateBox extends StatelessWidget {
  const _DateBox({required this.label, required this.value, required this.onTap});

  final String label;
  final DateTime? value;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
          suffixIcon: Icon(PhosphorIcons.calendarBlank(), size: 18),
        ),
        child: Text(value == null ? 'Choose' : DateFormat('d MMM yyyy').format(value!)),
      ),
    );
  }
}

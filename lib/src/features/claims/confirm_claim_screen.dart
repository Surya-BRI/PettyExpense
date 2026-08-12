import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../widgets/brand_app_bar.dart';

class ConfirmClaimScreen extends ConsumerStatefulWidget {
  const ConfirmClaimScreen({
    super.key,
    required this.ocr,
    this.localPath,
  });

  final OcrResult ocr;
  final String? localPath;

  @override
  ConsumerState<ConfirmClaimScreen> createState() => _ConfirmClaimScreenState();
}

class _ConfirmClaimScreenState extends ConsumerState<ConfirmClaimScreen> {
  late final TextEditingController _vendor;
  late final TextEditingController _amount;
  late final TextEditingController _date;
  late final TextEditingController _remarks;
  int? _categoryId;
  int? _projectId;
  String _type = 'reimbursement';
  bool _busy = false;
  String? _error;
  List<CategoryRef> _categories = const [];
  List<ProjectRef> _projects = const [];

  @override
  void initState() {
    super.initState();
    _vendor = TextEditingController(text: widget.ocr.vendor);
    _amount = TextEditingController(text: widget.ocr.amount.toStringAsFixed(2));
    _date = TextEditingController(text: widget.ocr.date);
    _remarks = TextEditingController();
    _loadReferenceData();
  }

  Future<void> _loadReferenceData() async {
    try {
      final api = ref.read(apiClientProvider);
      final categories = await api.categories();
      final projects = await api.projects();
      if (mounted) {
        setState(() {
          _categories = categories;
          _projects = projects;
          _categoryId ??= categories.isNotEmpty ? categories.first.id : null;
        });
      }
    } catch (_) {}
  }

  @override
  void dispose() {
    _vendor.dispose();
    _amount.dispose();
    _date.dispose();
    _remarks.dispose();
    super.dispose();
  }

  Future<void> _submit({required bool asDraft}) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final amount = double.tryParse(_amount.text.trim());
      if (amount == null) {
        throw Exception('Enter a valid amount');
      }
      if (_categoryId == null) {
        throw Exception('Select a category');
      }
      final api = ref.read(apiClientProvider);
      final claim = await api.createClaim({
        'vendor': _vendor.text.trim(),
        'amount': amount,
        'bill_date': _date.text.trim(),
        'category_id': _categoryId,
        'region_code': 'IN',
        'type': _type,
        'project_id': _projectId,
        'remarks': _remarks.text.trim().isEmpty ? null : _remarks.text.trim(),
        'receipt_id': widget.ocr.receiptId,
        's3_key': widget.ocr.s3Key,
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
    return Scaffold(
      appBar: const BrandAppBar(
        title: 'Confirm claim',
        automaticallyImplyLeading: true,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          if (widget.localPath != null)
            ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: Image.file(
                File(widget.localPath!),
                height: 200,
                width: double.infinity,
                fit: BoxFit.cover,
              ),
            ),
          if (widget.ocr.duplicateWarning != null) ...[
            const SizedBox(height: 12),
            Material(
              color: AppColors.warningSoft,
              borderRadius: BorderRadius.circular(12),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text(widget.ocr.duplicateWarning!.message),
              ),
            ),
          ],
          const SizedBox(height: 12),
          const Text('Please check and confirm the bill details before submitting.'),
          const SizedBox(height: 16),
          TextField(controller: _vendor, decoration: const InputDecoration(labelText: 'Vendor / provider')),
          const SizedBox(height: 12),
          TextField(
            controller: _amount,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(labelText: 'Amount (INR)'),
          ),
          const SizedBox(height: 12),
          TextField(controller: _date, decoration: const InputDecoration(labelText: 'Bill date')),
          const SizedBox(height: 12),
          InputDecorator(
            decoration: const InputDecoration(labelText: 'Type'),
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
            decoration: const InputDecoration(labelText: 'Category'),
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
          const SizedBox(height: 12),
          InputDecorator(
            decoration: const InputDecoration(labelText: 'Project / OP (optional)'),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<int?>(
                isExpanded: true,
                value: _projectId,
                items: [
                  const DropdownMenuItem(value: null, child: Text('Non-project / General')),
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
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          const SizedBox(height: 20),
          FilledButton(
            onPressed: _busy ? null : () => _submit(asDraft: false),
            child: Text(_busy ? 'Submitting…' : 'Submit for approval'),
          ),
          const SizedBox(height: 10),
          OutlinedButton(
            onPressed: _busy ? null : () => _submit(asDraft: true),
            child: const Text('Save as draft'),
          ),
        ],
      ),
    );
  }
}

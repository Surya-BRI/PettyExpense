// Employee petty cash advances (Professional Signs / companies with pca_model "employee").
//
// One advance per employee, used for all their projects.
// PCA amount: the employee's HOD (or Admin) sets it; live at once. It's a limit, not cash, so
//          there's no approval or payment -- money moves only when a top-up or reimbursement is paid.
// Top-up:  employee raises with approved bills -> HOD approves -> Accounts Manager verifies
//          -> Accounts Manager pays (cash withdrawal from bank, or direct payment).
// Report:  advances by department (with the employees), and petty-cash spend by project
//          (from the OP code on each bill).
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../api/enums.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../utils/money.dart';
import '../../widgets/app_nav_drawer.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/pca_fund_figures.dart';
import '../admin/admin_providers.dart';
import '../admin/my_funds_screen.dart' show myFundsProvider;
import '../authentication/auth_controller.dart';
import '../payments/payment_sheet.dart' show kPaymentMethods;
import 'accounts_cash_view.dart';

final pcaRequestsProvider = FutureProvider.autoDispose<List<TopupRequest>>((ref) {
  return ref.watch(apiClientProvider).pcaRequests();
});

final pcaAdvancesProvider = FutureProvider.autoDispose<List<PettyCashFund>>((ref) {
  return ref.watch(apiClientProvider).pcaAdvances();
});

/// The signed-in person's own petty cash (PCA) in employee-advance companies -- in any company
/// they cover, not only the one signed in under -- so someone in Dubai and KSA sees their KSA
/// petty cash from Dubai too. Skips the request for single-company people outside KSA.
final myPcaAdvancesProvider = FutureProvider.autoDispose<List<PettyCashFund>>((ref) async {
  final user = ref.watch(authControllerProvider).user;
  if (user == null) return const [];
  if (!user.usesEmployeeAdvances && user.allowedRegions.length <= 1) return const [];
  final all = await ref.watch(pcaAdvancesProvider.future);
  return [for (final f in all) if (f.employeeId == user.id && f.approvedLimit > 0) f];
});

final pcaSummaryProvider = FutureProvider.autoDispose.family<PcaSummary, int>((ref, regionId) {
  return ref.watch(apiClientProvider).pcaSummary(regionId);
});

/// Companies that give employee advances, in the usual company order.
final pcaRegionsProvider = FutureProvider.autoDispose<List<RegionConfig>>((ref) async {
  final regions = await ref.watch(adminRegionsProvider.future);
  return [for (final r in regions) if (r.usesEmployeeAdvances) r];
});

/// Employees tab: departments with counts (light).
final pcaDepartmentsProvider = FutureProvider.autoDispose.family<PcaDepartments, int>((ref, regionId) {
  return ref.watch(apiClientProvider).pcaDepartments(regionId);
});

/// One department's employees, loaded when the department is opened.
final pcaDepartmentEmployeesProvider = FutureProvider.autoDispose
    .family<PcaDepartmentEmployees, ({int regionId, int departmentId})>((ref, key) {
  return ref.watch(apiClientProvider).pcaDepartmentEmployees(key.regionId, key.departmentId);
});

void invalidatePcaProviders(WidgetRef ref) {
  ref.invalidate(pcaDepartmentsProvider);
  ref.invalidate(pcaDepartmentEmployeesProvider);
  ref.invalidate(pcaRequestsProvider);
  ref.invalidate(pcaAdvancesProvider);
  ref.invalidate(myPcaAdvancesProvider);
  ref.invalidate(pcaSummaryProvider);
  ref.invalidate(myFundsProvider);
  ref.invalidate(accountsCashProvider);
}

const kPaymentSources = <String, String>{
  'bank': 'Cash withdrawal from bank',
  'accounts_petty_cash': 'Direct payment by Accounts Department',
};

String pcaStatusLabel(TopupRequest r) {
  switch (r.status) {
    case 'submitted':
      return r.isAdvance ? 'Waiting for Accounts Manager' : 'Waiting for HOD';
    case 'hod_approved':
      return 'Waiting for Accounts Manager';
    case 'approved':
    case 'verified':
      return 'Waiting for payment';
    case 'paid':
      return 'Paid';
    case 'set':
      return r.amount < 0 ? 'Amount lowered' : 'Amount set';
    case 'rejected':
      return 'Rejected';
    default:
      return r.status;
  }
}

String pcaActionLabel(String action, {required bool advance}) {
  switch (action) {
    case 'requested':
      return advance ? 'Proposed' : 'Requested';
    case 'hod_approved':
      return 'Approved by HOD';
    case 'approved':
      return 'Approved by Accounts Manager';
    case 'verified':
      return 'Verified by Accounts Manager';
    case 'paid':
      return 'Paid';
    case 'set':
      return 'Petty cash amount set';
    case 'rejected':
      return 'Rejected';
    default:
      return action;
  }
}

enum _PcaAction { hodApprove, managerApprove, pay }

/// What the signed-in person can do on this request right now (mirrors the backend rules;
/// the server still checks).
Set<_PcaAction> _actionsFor(TopupRequest r, UserRole role) {
  final admin = role == UserRole.admin;
  final out = <_PcaAction>{};
  if (!r.isAdvance && r.status == 'submitted' && (role == UserRole.hod || admin)) {
    out.add(_PcaAction.hodApprove);
  }
  final managerStep = (r.isAdvance && r.status == 'submitted') || (!r.isAdvance && r.status == 'hod_approved');
  if (managerStep && (role == UserRole.financeManager || admin)) out.add(_PcaAction.managerApprove);
  final payStep = (r.isAdvance && r.status == 'approved') || (!r.isAdvance && r.status == 'verified');
  // Only the Accounts Manager pays in an employee-advance company.
  if (payStep && (role == UserRole.financeManager || admin)) out.add(_PcaAction.pay);
  return out;
}

String _when(DateTime? at) {
  if (at == null) return '';
  return DateFormat('d MMM yyyy, HH:mm').format(at.toLocal());
}

class AdvancesScreen extends ConsumerWidget {
  const AdvancesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    final role = UserRoleX.fromJson(user?.role);
    if (role == UserRole.employee) {
      return Scaffold(
        backgroundColor: AppColors.background,
        drawer: const AppNavDrawer(),
        appBar: const BrandAppBar(title: 'My advances', automaticallyImplyLeading: true),
        body: const _MyAdvancesView(),
      );
    }
    // The Accounts Department's own petty cash (PDF section 6): Accounts Manager, Accounts, Admin.
    final accountsCash =
        role == UserRole.financeManager || role == UserRole.accountant || role == UserRole.admin;
    // Petty cash is set from Employees -> department -> an employee (no separate button).
    return DefaultTabController(
      length: accountsCash ? 3 : 2,
      child: Scaffold(
        backgroundColor: AppColors.background,
        drawer: const AppNavDrawer(),
        appBar: const BrandAppBar(title: 'Advances', automaticallyImplyLeading: true),
        body: Column(
          children: [
            Material(
              color: AppColors.card,
              child: TabBar(
                labelColor: AppColors.darkBlue,
                unselectedLabelColor: AppColors.textSecondary,
                indicatorColor: AppColors.orange,
                tabs: [
                  const Tab(text: 'Employees'),
                  const Tab(text: 'Requests'),
                  if (accountsCash) const Tab(text: 'Accounts cash'),
                ],
              ),
            ),
            Expanded(
              child: TabBarView(
                children: [
                  // Every employee (by department) with their petty cash limit, spent and left.
                  _CompanyPicker(builder: (id) => PcaDepartmentsView(regionId: id)),
                  const PcaRequestsView(),
                  if (accountsCash) _CompanyPicker(builder: (id) => AccountsCashView(regionId: id)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Picks the employee-advance company to report on: the one signed in under, or (several
/// covered, e.g. Admin) chips to switch.
class _CompanyPicker extends ConsumerStatefulWidget {
  const _CompanyPicker({required this.builder});

  final Widget Function(int regionId) builder;

  @override
  ConsumerState<_CompanyPicker> createState() => _CompanyPickerState();
}

class _CompanyPickerState extends ConsumerState<_CompanyPicker> {
  int? _regionId;

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(pcaRegionsProvider);
    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('$e')),
      data: (regions) {
        if (regions.isEmpty) {
          return const Center(child: Text('No company gives employee advances.'));
        }
        final current = (ref.read(authControllerProvider).user?.regionCode ?? '').toUpperCase();
        final picked = _regionId ??
            regions
                .firstWhere((r) => r.regionCode.toUpperCase() == current, orElse: () => regions.first)
                .id;
        return Column(
          children: [
            if (regions.length > 1)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                child: Wrap(
                  spacing: 8,
                  children: [
                    for (final r in regions)
                      ChoiceChip(
                        label: Text(companyTitle(r)),
                        selected: r.id == picked,
                        onSelected: (_) => setState(() => _regionId = r.id),
                      ),
                  ],
                ),
              ),
            Expanded(child: widget.builder(picked)),
          ],
        );
      },
    );
  }
}

// ---- requests ------------------------------------------------------------------------------

class PcaRequestsView extends ConsumerStatefulWidget {
  const PcaRequestsView({super.key});

  @override
  ConsumerState<PcaRequestsView> createState() => _PcaRequestsViewState();
}

class _PcaRequestsViewState extends ConsumerState<PcaRequestsView> {
  bool _mineOnly = true;

  @override
  Widget build(BuildContext context) {
    final role = UserRoleX.fromJson(ref.watch(authControllerProvider).user?.role);
    final async = ref.watch(pcaRequestsProvider);
    return RefreshIndicator(
      onRefresh: () async => invalidatePcaProviders(ref),
      child: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => ListView(children: [Padding(padding: const EdgeInsets.all(24), child: Text('$e'))]),
        data: (all) {
          final waiting = [for (final r in all) if (_actionsFor(r, role).isNotEmpty) r];
          final items = _mineOnly ? waiting : all;
          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 96),
            children: [
              Wrap(
                spacing: 8,
                children: [
                  ChoiceChip(
                    label: Text('Active (${waiting.length})'),
                    selected: _mineOnly,
                    onSelected: (_) => setState(() => _mineOnly = true),
                  ),
                  ChoiceChip(
                    label: Text('History (${all.length})'),
                    selected: !_mineOnly,
                    onSelected: (_) => setState(() => _mineOnly = false),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (items.isEmpty)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 32),
                  child: Text(
                    _mineOnly ? 'Nothing is waiting for you.' : 'No history yet.',
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: AppColors.textSecondary),
                  ),
                )
              else
                for (final r in items) ...[PcaRequestTile(request: r), const SizedBox(height: 10)],
            ],
          );
        },
      ),
    );
  }
}

class PcaRequestTile extends ConsumerStatefulWidget {
  const PcaRequestTile({super.key, required this.request});

  final TopupRequest request;

  @override
  ConsumerState<PcaRequestTile> createState() => _PcaRequestTileState();
}

class _PcaRequestTileState extends ConsumerState<PcaRequestTile> {
  bool _busy = false;

  Future<void> _run(Future<void> Function() action) async {
    setState(() => _busy = true);
    try {
      await action();
      invalidatePcaProviders(ref);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _reject() async {
    final reason = await showDialog<String>(context: context, builder: (_) => const _ReasonDialog());
    if (reason == null || reason.isEmpty || !mounted) return;
    await _run(() => ref.read(apiClientProvider).pcaStep(widget.request.id, 'reject', remarks: reason));
  }

  Future<void> _pay() async {
    final paid = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => _PayRequestSheet(request: widget.request),
    );
    if (paid == true) invalidatePcaProviders(ref);
  }

  @override
  Widget build(BuildContext context) {
    final r = widget.request;
    final role = UserRoleX.fromJson(ref.watch(authControllerProvider).user?.role);
    final actions = _actionsFor(r, role);
    final fund = r.fund;
    final currency = fund?.currency ?? '';
    final project = fund?.projectLabel;
    final done = r.status == 'paid';
    final rejected = r.status == 'rejected';
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: r.isAdvance ? AppColors.lightBlue : AppColors.warningSoft,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    r.isAdvance ? 'PETTY CASH' : 'TOP-UP',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800, letterSpacing: 0.4),
                  ),
                ),
                const Spacer(),
                Text(
                  pcaStatusLabel(r),
                  style: TextStyle(
                    fontSize: 12.5,
                    fontWeight: FontWeight.w700,
                    color: done
                        ? AppColors.success
                        : rejected
                            ? AppColors.danger
                            : AppColors.orange,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              formatMoney(currency, r.amount),
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 20, color: AppColors.darkBlue),
            ),
            const SizedBox(height: 4),
            Text(
              r.employeeName ?? fund?.employeeName ?? 'Employee',
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
            ),
            if (project != null)
              Text(project, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            if (r.transactionIds.isNotEmpty)
              Text(
                '${r.transactionIds.length} approved bill${r.transactionIds.length == 1 ? '' : 's'}',
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 12.5),
              ),
            if ((r.remarks ?? '').trim().isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(r.remarks!.trim(), style: const TextStyle(fontSize: 13)),
            ],
            if (done && (r.paymentReference ?? '').isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                [
                  kPaymentSources[r.paymentSource] ?? r.paymentSource,
                  'ref ${r.paymentReference}',
                ].whereType<String>().join(' · '),
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 12.5),
              ),
            ],
            if (r.history.isNotEmpty) _History(entries: r.history, advance: r.isAdvance),
            if (actions.isNotEmpty) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: actions.contains(_PcaAction.pay)
                        ? FilledButton.icon(
                            onPressed: _busy ? null : _pay,
                            style: FilledButton.styleFrom(backgroundColor: AppColors.success),
                            icon: Icon(PhosphorIcons.money(), size: 18),
                            label: const Text('Record payment'),
                          )
                        : FilledButton(
                            onPressed: _busy
                                ? null
                                : () => _run(() => ref.read(apiClientProvider).pcaStep(
                                      r.id,
                                      actions.contains(_PcaAction.hodApprove) ? 'hod-approve' : 'manager-approve',
                                    )),
                            child: Text(
                              actions.contains(_PcaAction.hodApprove)
                                  ? 'Approve'
                                  : r.isAdvance
                                      ? 'Approve advance'
                                      : 'Verify',
                            ),
                          ),
                  ),
                  if (!actions.contains(_PcaAction.pay) || role == UserRole.admin) ...[
                    const SizedBox(width: 8),
                    Expanded(
                      child: OutlinedButton(onPressed: _busy ? null : _reject, child: const Text('Reject')),
                    ),
                  ],
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _History extends StatelessWidget {
  const _History({required this.entries, required this.advance});

  final List<TopupHistoryEntry> entries;
  final bool advance;

  @override
  Widget build(BuildContext context) {
    return Theme(
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        tilePadding: EdgeInsets.zero,
        childrenPadding: const EdgeInsets.only(bottom: 4),
        title: Text(
          'History (${entries.length})',
          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.darkBlue),
        ),
        children: [
          for (final h in entries.reversed)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 5),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          [pcaActionLabel(h.action, advance: advance), if ((h.actorName ?? '').isNotEmpty) h.actorName!]
                              .join(' · '),
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                        ),
                        if ((h.comment ?? '').trim().isNotEmpty)
                          Text(h.comment!.trim(),
                              style: const TextStyle(fontSize: 12.5, color: AppColors.textSecondary)),
                      ],
                    ),
                  ),
                  Text(_when(h.at), style: const TextStyle(fontSize: 11.5, color: AppColors.textSecondary)),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _ReasonDialog extends StatefulWidget {
  const _ReasonDialog();

  @override
  State<_ReasonDialog> createState() => _ReasonDialogState();
}

class _ReasonDialogState extends State<_ReasonDialog> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final text = _controller.text.trim();
    return AlertDialog(
      title: const Text('Reject'),
      content: TextField(
        controller: _controller,
        autofocus: true,
        maxLines: 3,
        onChanged: (_) => setState(() {}),
        decoration: const InputDecoration(labelText: 'Reason *'),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Cancel')),
        FilledButton(
          onPressed: text.isEmpty ? null : () => Navigator.of(context).pop(text),
          child: const Text('Reject'),
        ),
      ],
    );
  }
}

/// The Accounts Manager records how an approved advance / top-up was paid.
class _PayRequestSheet extends ConsumerStatefulWidget {
  const _PayRequestSheet({required this.request});

  final TopupRequest request;

  @override
  ConsumerState<_PayRequestSheet> createState() => _PayRequestSheetState();
}

class _PayRequestSheetState extends ConsumerState<_PayRequestSheet> {
  final _reference = TextEditingController();
  final _remarks = TextEditingController();
  String _source = 'bank';
  String _method = 'bank_transfer';
  DateTime _date = DateUtils.dateOnly(DateTime.now());
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _reference.dispose();
    _remarks.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final reference = _reference.text.trim();
    if (reference.isEmpty) {
      setState(() => _error = 'Enter the payment reference');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).pcaPay(
            widget.request.id,
            source: _source,
            method: _method,
            reference: reference,
            paymentDate: DateFormat('yyyy-MM-dd').format(_date),
            remarks: _remarks.text.trim().isEmpty ? null : _remarks.text.trim(),
          );
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final r = widget.request;
    final currency = r.fund?.currency ?? '';
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 20, 20, 20 + MediaQuery.viewInsetsOf(context).bottom),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(r.isAdvance ? 'Pay advance' : 'Pay top-up', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(
              [r.employeeName ?? r.fund?.employeeName, r.fund?.projectLabel].whereType<String>().join(' · '),
              style: const TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 12),
            Text(
              formatMoney(currency, r.amount),
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppColors.darkBlue),
            ),
            const SizedBox(height: 12),
            const Text('Paid from', style: TextStyle(fontWeight: FontWeight.w700)),
            RadioGroup<String>(
              groupValue: _source,
              onChanged: (v) {
                if (!_busy) setState(() => _source = v ?? _source);
              },
              child: Column(
                children: [
                  for (final e in kPaymentSources.entries)
                    RadioListTile<String>(
                      contentPadding: EdgeInsets.zero,
                      dense: true,
                      value: e.key,
                      title: Text(e.value),
                    ),
                ],
              ),
            ),
            DropdownButtonFormField<String>(
              initialValue: _method,
              decoration: const InputDecoration(labelText: 'Payment method'),
              items: [for (final e in kPaymentMethods.entries) DropdownMenuItem(value: e.key, child: Text(e.value))],
              onChanged: _busy ? null : (v) => setState(() => _method = v ?? _method),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _reference,
              enabled: !_busy,
              decoration: const InputDecoration(
                labelText: 'Payment reference *',
                hintText: 'Transfer or withdrawal number',
              ),
            ),
            const SizedBox(height: 12),
            InkWell(
              onTap: _busy
                  ? null
                  : () async {
                      final picked = await showDatePicker(
                        context: context,
                        initialDate: _date,
                        firstDate: DateTime.now().subtract(const Duration(days: 365)),
                        lastDate: DateUtils.dateOnly(DateTime.now()),
                      );
                      if (picked != null) setState(() => _date = picked);
                    },
              child: InputDecorator(
                decoration: const InputDecoration(labelText: 'Payment date'),
                child: Text(DateFormat('d MMM yyyy').format(_date)),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _remarks,
              enabled: !_busy,
              decoration: const InputDecoration(labelText: 'Remarks (optional)'),
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: AppColors.danger)),
            ],
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: _busy ? null : _save,
              style: FilledButton.styleFrom(
                backgroundColor: AppColors.success,
                minimumSize: const Size.fromHeight(48),
              ),
              icon: Icon(PhosphorIcons.checkCircle(), size: 20),
              label: const Text('Mark as paid'),
            ),
          ],
        ),
      ),
    );
  }
}

// ---- Employees: departments, then one department's people --------------------------------

/// Employees tab: just the departments (counts and total limit -- one light request). Tapping
/// one opens its employees, loaded only then.
class PcaDepartmentsView extends ConsumerWidget {
  const PcaDepartmentsView({super.key, required this.regionId});

  final int regionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(pcaDepartmentsProvider(regionId));
    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(pcaDepartmentsProvider(regionId)),
      child: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => ListView(children: [Padding(padding: const EdgeInsets.all(24), child: Text('$e'))]),
        data: (d) {
          if (d.departments.isEmpty) {
            return ListView(
              children: const [
                Padding(
                  padding: EdgeInsets.all(32),
                  child: Text('No employees.', textAlign: TextAlign.center),
                ),
              ],
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 96),
            itemCount: d.departments.length,
            separatorBuilder: (_, _) => const SizedBox(height: 10),
            itemBuilder: (context, i) {
              final dept = d.departments[i];
              return _DepartmentTile(
                department: dept,
                currency: d.currency,
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => PcaDepartmentEmployeesScreen(regionId: regionId, department: dept),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

class _DepartmentTile extends StatelessWidget {
  const _DepartmentTile({required this.department, required this.currency, required this.onTap});

  final PcaDepartment department;
  final String currency;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final d = department;
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(14, 14, 10, 14),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(color: AppColors.lightBlue, borderRadius: BorderRadius.circular(12)),
                child: Icon(PhosphorIcons.usersThree(), color: AppColors.darkBlue, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      d.name,
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15.5, color: AppColors.darkBlue),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      '${d.employeeCount} employee${d.employeeCount == 1 ? '' : 's'} · '
                      '${d.withPettyCash} with petty cash',
                      style: const TextStyle(fontSize: 12.5, color: AppColors.textSecondary),
                    ),
                    if (d.notSet > 0) ...[
                      const SizedBox(height: 4),
                      Text(
                        '${d.notSet} not set',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.orange),
                      ),
                    ],
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    formatMoney(currency, d.totalLimit),
                    style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13.5),
                  ),
                  const Text('total limit', style: TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                ],
              ),
              const SizedBox(width: 4),
              Icon(PhosphorIcons.caretRight(), color: AppColors.textSecondary, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}

/// One department's employees with their limit, what's left and a usage bar; "Not set" people
/// get a Set button (HOD / Admin).
class PcaDepartmentEmployeesScreen extends ConsumerStatefulWidget {
  const PcaDepartmentEmployeesScreen({super.key, required this.regionId, required this.department});

  final int regionId;
  final PcaDepartment department;

  @override
  ConsumerState<PcaDepartmentEmployeesScreen> createState() => _PcaDepartmentEmployeesScreenState();
}

class _PcaDepartmentEmployeesScreenState extends ConsumerState<PcaDepartmentEmployeesScreen> {
  bool _notSetOnly = false;
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final key = (regionId: widget.regionId, departmentId: widget.department.departmentId);
    final async = ref.watch(pcaDepartmentEmployeesProvider(key));
    final role = UserRoleX.fromJson(ref.watch(authControllerProvider).user?.role);
    final canSet = role == UserRole.hod || role == UserRole.admin;

    Future<void> setFor(PcaMember m) async {
      if (m.employeeId == null) return;
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ProposeAdvanceScreen(initialRegionId: widget.regionId, initialEmployeeId: m.employeeId),
        ),
      );
      invalidatePcaProviders(ref);
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: BrandAppBar(title: widget.department.name, automaticallyImplyLeading: true, showMenuAction: false),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(pcaDepartmentEmployeesProvider(key)),
        child: async.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => ListView(children: [Padding(padding: const EdgeInsets.all(24), child: Text('$e'))]),
          data: (d) {
            final notSet = d.employees.where((m) => m.figures.advance <= 0).length;
            final q = _query.trim().toLowerCase();
            final people = [
              for (final m in d.employees)
                if ((!_notSetOnly || m.figures.advance <= 0) &&
                    (q.isEmpty || (m.employeeName ?? '').toLowerCase().contains(q)))
                  m,
            ];
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
              children: [
                if (d.employees.length > 8) ...[
                  TextField(
                    decoration: InputDecoration(
                      prefixIcon: Icon(PhosphorIcons.magnifyingGlass(), size: 18),
                      hintText: 'Search employee',
                      isDense: true,
                    ),
                    onChanged: (v) => setState(() => _query = v),
                  ),
                  const SizedBox(height: 8),
                ],
                Wrap(
                  spacing: 8,
                  children: [
                    ChoiceChip(
                      label: Text('All (${d.employees.length})'),
                      selected: !_notSetOnly,
                      onSelected: (_) => setState(() => _notSetOnly = false),
                    ),
                    if (notSet > 0)
                      ChoiceChip(
                        avatar: Icon(PhosphorIcons.warningCircle(), size: 16, color: AppColors.orange),
                        label: Text('Not set ($notSet)'),
                        selected: _notSetOnly,
                        onSelected: (_) => setState(() => _notSetOnly = true),
                      ),
                  ],
                ),
                const SizedBox(height: 10),
                if (people.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 32),
                    child: Text('Nobody matches.', textAlign: TextAlign.center),
                  ),
                for (final m in people) ...[
                  _EmployeeCard(member: m, currency: d.currency, onSet: canSet ? setFor : null),
                  const SizedBox(height: 8),
                ],
              ],
            );
          },
        ),
      ),
    );
  }
}

class _EmployeeCard extends StatelessWidget {
  const _EmployeeCard({required this.member, required this.currency, this.onSet});

  final PcaMember member;
  final String currency;
  final void Function(PcaMember member)? onSet;

  @override
  Widget build(BuildContext context) {
    final m = member;
    final f = m.figures;
    final isSet = f.advance > 0;
    final used = isSet ? ((f.advance - f.available) / f.advance).clamp(0.0, 1.0) : 0.0;
    final name = (m.employeeName ?? 'Employee').trim();
    final initial = name.isEmpty ? '?' : name[0].toUpperCase();
    final extras = [
      if (f.unreplenishedSpend > 0) 'to top up ${formatMoney(currency, f.unreplenishedSpend)}',
      if (f.pendingBills > 0) 'in approval ${formatMoney(currency, f.pendingBills)}',
    ];
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onSet == null ? null : () => onSet!(m),
        child: Container(
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: isSet ? AppColors.divider : AppColors.orange.withValues(alpha: 0.45)),
          ),
          child: Row(
            children: [
              CircleAvatar(
                radius: 18,
                backgroundColor: isSet ? AppColors.lightBlue : AppColors.warningSoft,
                child: Text(
                  initial,
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    color: isSet ? AppColors.darkBlue : AppColors.orange,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(name, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14.5)),
                    const SizedBox(height: 2),
                    if (isSet) ...[
                      Text(
                        'limit ${formatMoney(currency, f.advance)} · spent ${formatMoney(currency, f.spent)}',
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                      if (extras.isNotEmpty)
                        Text(extras.join(' · '), style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                      const SizedBox(height: 6),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(
                          value: used,
                          minHeight: 5,
                          backgroundColor: AppColors.lightBlue,
                          color: used >= 0.5 ? AppColors.orange : AppColors.success,
                        ),
                      ),
                    ] else
                      Text(
                        f.advanceWaiting > 0
                            ? 'Waiting: ${formatMoney(currency, f.advanceWaiting)} proposed'
                            : 'No petty cash · bills go as reimbursements',
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              if (isSet)
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      formatMoney(currency, f.available),
                      style: TextStyle(
                        fontWeight: FontWeight.w800,
                        fontSize: 14,
                        color: used >= 0.5 ? AppColors.orange : AppColors.darkBlue,
                      ),
                    ),
                    const Text('left', style: TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                  ],
                )
              else if (onSet != null)
                OutlinedButton(
                  onPressed: () => onSet!(m),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.orange,
                    side: const BorderSide(color: AppColors.orange),
                    padding: const EdgeInsets.symmetric(horizontal: 14),
                    minimumSize: const Size(0, 34),
                    visualDensity: VisualDensity.compact,
                  ),
                  child: const Text('Set'),
                )
              else
                const Text('Not set', style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.orange)),
            ],
          ),
        ),
      ),
    );
  }
}

// ---- employee: my advances -----------------------------------------------------------------

class _MyAdvancesView extends ConsumerWidget {
  const _MyAdvancesView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final advances = ref.watch(pcaAdvancesProvider);
    final requests = ref.watch(pcaRequestsProvider);
    return RefreshIndicator(
      onRefresh: () async => invalidatePcaProviders(ref),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
        children: [
          advances.when(
            loading: () => const Padding(
              padding: EdgeInsets.all(32),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (e, _) => Text('$e'),
            data: (funds) {
              final paid = [for (final f in funds) if (f.approvedLimit > 0) f];
              if (paid.isEmpty) {
                return Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(14)),
                  child: const Text(
                    'You have no petty cash yet. Your HOD sets the amount. '
                    'Until then, file bills as reimbursements.',
                    style: TextStyle(color: AppColors.textSecondary, height: 1.35),
                  ),
                );
              }
              return Column(
                children: [
                  for (final f in paid) ...[_MyAdvanceCard(fund: f), const SizedBox(height: 12)],
                ],
              );
            },
          ),
          const SizedBox(height: 8),
          const Text(
            'Requests',
            style: TextStyle(color: AppColors.darkBlue, fontWeight: FontWeight.w800, fontSize: 13, letterSpacing: 0.3),
          ),
          const SizedBox(height: 8),
          ...requests.when(
            loading: () => const [Center(child: CircularProgressIndicator())],
            error: (e, _) => [Text('$e')],
            data: (rows) => rows.isEmpty
                ? const [Text('No requests yet.', style: TextStyle(color: AppColors.textSecondary))]
                : [for (final r in rows) ...[PcaRequestTile(request: r), const SizedBox(height: 10)]],
          ),
        ],
      ),
    );
  }
}

class _MyAdvanceCard extends ConsumerWidget {
  const _MyAdvanceCard({required this.fund});

  final PettyCashFund fund;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(16),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Petty cash advance',
              style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18, color: AppColors.darkBlue),
            ),
            Text(
              [fund.regionCode, 'for all your projects'].whereType<String>().join(' · '),
              style: const TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 12),
            PcaFundFigures(fund: fund, compact: true),
            // No top-up request: the Accounts Manager pays approved bills from Payments (PDF
            // section 7, Process 1 / 2), which refills the petty cash.
            if (fund.unreplenishedSpend > 0) ...[
              const SizedBox(height: 8),
              Text(
                '${formatMoney(fund.currency, fund.unreplenishedSpend)} of approved bills waiting for '
                'Accounts to pay. Your petty cash is refilled when they do.',
                style: const TextStyle(fontSize: 12.5),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// ---- forms ---------------------------------------------------------------------------------

/// HOD (or Admin) sets the petty cash (PCA) amount for one of their staff: one per employee, for
/// all their projects. Live at once -- no approval or payment. Setting again changes it.
class ProposeAdvanceScreen extends ConsumerStatefulWidget {
  const ProposeAdvanceScreen({super.key, this.initialRegionId, this.initialEmployeeId});

  /// Opened from an employee in the Employees list: that company and person are preselected.
  final int? initialRegionId;
  final int? initialEmployeeId;

  @override
  ConsumerState<ProposeAdvanceScreen> createState() => _ProposeAdvanceScreenState();
}

class _ProposeAdvanceScreenState extends ConsumerState<ProposeAdvanceScreen> {
  final _amount = TextEditingController();
  final _remarks = TextEditingController();
  int? _regionId;
  List<PcaStaff> _staff = const [];
  int? _employeeId;
  bool _loadingStaff = false;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _amount.dispose();
    _remarks.dispose();
    super.dispose();
  }

  Future<void> _loadStaff(int regionId) async {
    setState(() {
      _regionId = regionId;
      _loadingStaff = true;
      _staff = const [];
      _employeeId = null;
      _error = null;
    });
    try {
      final staff = await ref.read(apiClientProvider).pcaStaff(regionId);
      if (mounted) {
        final wanted = widget.initialEmployeeId;
        setState(() => _staff = staff);
        if (wanted != null && staff.any((s) => s.id == wanted)) _pickEmployee(wanted);
      }
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _loadingStaff = false);
    }
  }

  bool get _multiDepartment => _staff.map((s) => s.departmentName).toSet().length > 1;

  /// Picks the employee and fills in their current amount (empty when not set yet).
  void _pickEmployee(int? id) {
    final current = _staff.where((s) => s.id == id).firstOrNull?.advance ?? 0;
    setState(() {
      _employeeId = id;
      _amount.text = current > 0 ? current.toStringAsFixed(2) : '';
    });
  }

  Future<void> _save() async {
    final amount = double.tryParse(_amount.text.trim().replaceAll(',', ''));
    final problem = _regionId == null
        ? 'Pick the company'
        : _employeeId == null
            ? 'Pick the employee'
            : (amount == null || amount < 0)
                ? 'Enter the petty cash amount'
                : null;
    if (problem != null) {
      setState(() => _error = problem);
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).proposeAdvance(
            regionId: _regionId!,
            employeeId: _employeeId!,
            amount: amount!,
            remarks: _remarks.text.trim().isEmpty ? null : _remarks.text.trim(),
          );
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final regionsAsync = ref.watch(pcaRegionsProvider);
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: const BrandAppBar(title: 'Set petty cash', automaticallyImplyLeading: true, showMenuAction: false),
      body: regionsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (regions) {
          if (regions.isEmpty) return const Center(child: Text('No company gives employee advances.'));
          if (_regionId == null) {
            final current = (ref.read(authControllerProvider).user?.regionCode ?? '').toUpperCase();
            final pick = regions.where((r) => r.id == widget.initialRegionId).firstOrNull ??
                regions.firstWhere((r) => r.regionCode.toUpperCase() == current, orElse: () => regions.first);
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (mounted && _regionId == null) _loadStaff(pick.id);
            });
          }
          final region = regions.where((r) => r.id == _regionId).firstOrNull;
          final currency = region?.baseCurrency ?? '';
          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              if (regions.length > 1) ...[
                Wrap(
                  spacing: 8,
                  children: [
                    for (final r in regions)
                      ChoiceChip(
                        label: Text(companyTitle(r)),
                        selected: r.id == _regionId,
                        onSelected: _busy ? null : (_) => _loadStaff(r.id),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
              ],
              if (_loadingStaff)
                const LinearProgressIndicator()
              else
                DropdownButtonFormField<int>(
                  key: ValueKey('staff-$_regionId'),
                  isExpanded: true,
                  initialValue: _employeeId,
                  decoration: const InputDecoration(labelText: 'Employee *'),
                  items: [
                    for (final s in _staff)
                      DropdownMenuItem(
                        value: s.id,
                        child: Row(
                          children: [
                            Expanded(
                              child: Text(
                                // Department only when the list spans more than one.
                                [
                                  s.displayName,
                                  if (_multiDepartment && (s.departmentName ?? '').isNotEmpty) s.departmentName!,
                                ].join(' · '),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              s.advance > 0 ? formatMoney(currency, s.advance) : 'Not set',
                              style: TextStyle(
                                fontSize: 12.5,
                                fontWeight: FontWeight.w700,
                                color: s.advance > 0 ? AppColors.textSecondary : AppColors.orange,
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                  onChanged: _busy ? null : _pickEmployee,
                ),
              const SizedBox(height: 12),
              TextField(
                controller: _amount,
                enabled: !_busy,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(labelText: 'Petty cash amount *', suffixText: currency),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _remarks,
                enabled: !_busy,
                maxLines: 2,
                decoration: const InputDecoration(labelText: 'Why this amount (optional)'),
              ),
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(_error!, style: const TextStyle(color: AppColors.danger)),
              ],
              const SizedBox(height: 20),
              FilledButton(
                onPressed: _busy || _loadingStaff ? null : _save,
                style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(48)),
                child: Text(_busy ? 'Saving…' : 'Save'),
              ),
            ],
          );
        },
      ),
    );
  }
}

/// Employee (or HOD) asks to top up the employee's advance with its approved bills.
class RaiseAdvanceTopupScreen extends ConsumerStatefulWidget {
  const RaiseAdvanceTopupScreen({super.key, required this.fund});

  final PettyCashFund fund;

  @override
  ConsumerState<RaiseAdvanceTopupScreen> createState() => _RaiseAdvanceTopupScreenState();
}

class _RaiseAdvanceTopupScreenState extends ConsumerState<RaiseAdvanceTopupScreen> {
  final _remarks = TextEditingController();
  List<ReplenishableBill> _bills = const [];
  final Set<int> _selected = {};
  bool _loading = true;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _remarks.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final bills = await ref.read(apiClientProvider).pcaReplenishableBills(widget.fund.id);
      if (!mounted) return;
      setState(() {
        _bills = bills;
        _selected.addAll(bills.map((b) => b.id));
      });
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  double get _amount => _bills.where((b) => _selected.contains(b.id)).fold(0, (sum, b) => sum + b.amount);

  Future<void> _save() async {
    if (_selected.isEmpty) {
      setState(() => _error = 'Pick the approved bills to top up');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).pcaRequestTopup(
            widget.fund.id,
            transactionIds: _selected.toList(),
            remarks: _remarks.text.trim().isEmpty ? null : _remarks.text.trim(),
          );
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final fund = widget.fund;
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: const BrandAppBar(title: 'Raise top-up', automaticallyImplyLeading: true, showMenuAction: false),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                InputDecorator(
                  decoration: const InputDecoration(labelText: 'Advance'),
                  child: Text(
                    fund.projectLabel ?? [fund.employeeName, fund.regionCode].whereType<String>().join(' · '),
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  'Amount  ${formatMoney(fund.currency, _amount)}',
                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
                ),
                const SizedBox(height: 8),
                if (_bills.isEmpty)
                  const Text(
                    'No approved bills waiting for a top-up on this advance.',
                    style: TextStyle(color: AppColors.textSecondary),
                  )
                else
                  for (final bill in _bills)
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      value: _selected.contains(bill.id),
                      onChanged: (on) => setState(() {
                        if (on == true) {
                          _selected.add(bill.id);
                        } else {
                          _selected.remove(bill.id);
                        }
                      }),
                      title: Text(formatMoney(bill.currency ?? fund.currency, bill.amount)),
                      subtitle: Text(
                        [if ((bill.billDate ?? '').isNotEmpty) bill.billDate, '#${bill.id}']
                            .whereType<String>()
                            .join(' · '),
                      ),
                    ),
                const SizedBox(height: 12),
                TextField(
                  controller: _remarks,
                  decoration: const InputDecoration(labelText: 'Note (optional)'),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!, style: const TextStyle(color: AppColors.danger)),
                ],
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: _busy || _bills.isEmpty ? null : _save,
                  style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(48)),
                  child: Text(_busy ? 'Sending…' : 'Send to HOD'),
                ),
              ],
            ),
    );
  }
}

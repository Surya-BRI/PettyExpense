import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../widgets/app_nav_drawer.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/claim_ui_helpers.dart';
import '../../widgets/region_branding.dart';
import 'admin_providers.dart';

class AdminPeopleScreen extends ConsumerWidget {
  const AdminPeopleScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final regionsAsync = ref.watch(adminRegionsProvider);
    return Scaffold(
      backgroundColor: AppColors.background,
      drawer: const AppNavDrawer(),
      appBar: const BrandAppBar(title: 'People'),
      body: regionsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (regions) {
          if (regions.isEmpty) {
            return const Center(child: Text('No companies configured'));
          }
          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
            itemCount: regions.length,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, i) {
              final region = regions[i];
              return _PeopleCompanyCard(
                region: region,
                onTap: () => context.push('/admin/people/${region.regionCode}', extra: region),
              );
            },
          );
        },
      ),
    );
  }
}

class _PeopleCompanyCard extends StatelessWidget {
  const _PeopleCompanyCard({required this.region, required this.onTap});

  final RegionConfig region;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.card,
      elevation: 0,
      borderRadius: BorderRadius.circular(16),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              height: 92,
              color: const Color(0xFFF4F6F8),
              padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 18),
              child: RegionLogo(regionCode: region.regionCode, fit: BoxFit.contain, alignment: Alignment.center),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 12, 16),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          companyTitle(region),
                          style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, height: 1.25),
                        ),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 8,
                          runSpacing: 6,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: AppColors.lightBlue,
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                region.regionCode.toUpperCase(),
                                style: const TextStyle(
                                  color: AppColors.darkBlue,
                                  fontWeight: FontWeight.w700,
                                  fontSize: 11,
                                  letterSpacing: 0.4,
                                ),
                              ),
                            ),
                            const Text(
                              'Employee directory',
                              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  Icon(PhosphorIcons.caretRight(), color: AppColors.textSecondary, size: 18),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class AdminCompanyPeopleScreen extends ConsumerStatefulWidget {
  const AdminCompanyPeopleScreen({super.key, required this.regionCode, this.region});

  final String regionCode;
  final RegionConfig? region;

  @override
  ConsumerState<AdminCompanyPeopleScreen> createState() => _AdminCompanyPeopleScreenState();
}

class _AdminCompanyPeopleScreenState extends ConsumerState<AdminCompanyPeopleScreen> {
  static const _pageSize = 100;
  final _search = TextEditingController();
  final _listScroll = ScrollController();
  String _query = '';
  String? _department;
  bool _loading = true;
  String? _error;
  final List<OrgUser> _people = [];
  int _total = 0;
  int _page = 0;

  int get _pageCount => _total <= 0 ? 0 : ((_total + _pageSize - 1) ~/ _pageSize);
  bool get _hasPrev => _page > 0;
  bool get _hasNext => _page + 1 < _pageCount;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    _listScroll.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final page = await ref.read(apiClientProvider).adminUsers(
            regionCode: widget.regionCode,
            q: _query,
            limit: _pageSize,
            offset: _page * _pageSize,
          );
      if (!mounted) return;
      if (page.total > 0 && _page * _pageSize >= page.total) {
        setState(() {
          _total = page.total;
          _page = (page.total - 1) ~/ _pageSize;
        });
        await _load();
        return;
      }
      setState(() {
        _people
          ..clear()
          ..addAll(page.items);
        _total = page.total;
        _loading = false;
      });
      if (_listScroll.hasClients) {
        _listScroll.jumpTo(0);
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  void _applySearch(String raw) {
    final next = raw.trim();
    if (next == _query && _page == 0) return;
    setState(() {
      _query = next;
      _department = null;
      _page = 0;
    });
    _load();
  }

  List<String> get _departments {
    final names = <String>{};
    for (final u in _people) {
      final name = (u.departmentName ?? '').trim();
      if (name.isNotEmpty) names.add(name);
    }
    final out = names.toList()..sort((a, b) => a.toLowerCase().compareTo(b.toLowerCase()));
    return out;
  }

  List<OrgUser> get _visiblePeople {
    final dept = _department;
    if (dept == null) return _people;
    return [for (final u in _people) if ((u.departmentName ?? '').trim() == dept) u];
  }

  List<(String?, OrgUser?)> get _groupedRows {
    final byDept = <String, List<OrgUser>>{};
    for (final u in _visiblePeople) {
      final key = (u.departmentName ?? '').trim();
      byDept.putIfAbsent(key.isEmpty ? 'No department' : key, () => []).add(u);
    }
    final keys = byDept.keys.toList()
      ..sort((a, b) {
        if (a == 'No department') return 1;
        if (b == 'No department') return -1;
        return a.toLowerCase().compareTo(b.toLowerCase());
      });
    final rows = <(String?, OrgUser?)>[];
    for (final key in keys) {
      final members = byDept[key]!;
      rows.add(('$key · ${members.length}', null));
      for (final u in members) {
        rows.add((null, u));
      }
    }
    return rows;
  }

  void _goPage(int page) {
    if (_loading) return;
    final last = _pageCount <= 0 ? 0 : _pageCount - 1;
    final next = page.clamp(0, last);
    if (next == _page) return;
    setState(() => _page = next);
    _load();
  }

  Future<void> _openPerson(OrgUser user) async {
    await context.push(
      '/admin/people/${widget.regionCode}/${user.id}',
      extra: user,
    );
    if (mounted) await _load();
  }

  @override
  Widget build(BuildContext context) {
    final regions = ref.watch(adminRegionsProvider).valueOrNull ?? const <RegionConfig>[];
    RegionConfig? region = widget.region;
    if (region == null) {
      for (final r in regions) {
        if (r.regionCode.toUpperCase() == widget.regionCode.toUpperCase()) {
          region = r;
          break;
        }
      }
    }
    final title = region != null ? companyTitle(region) : widget.regionCode;
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: BrandAppBar(title: title, automaticallyImplyLeading: true, showMenuAction: false),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              controller: _search,
              onSubmitted: _applySearch,
              onChanged: (v) {
                if (v.trim().isEmpty && _query.isNotEmpty) _applySearch('');
              },
              textInputAction: TextInputAction.search,
              decoration: InputDecoration(
                hintText: 'Search name, department, or email',
                prefixIcon: Icon(PhosphorIcons.magnifyingGlass()),
                isDense: true,
                suffixIcon: IconButton(
                  icon: Icon(PhosphorIcons.magnifyingGlass()),
                  onPressed: () => _applySearch(_search.text),
                ),
              ),
            ),
          ),
          if (_departments.isNotEmpty)
            SizedBox(
              height: 40,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                children: [
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text('All (${_people.length})'),
                      selected: _department == null,
                      onSelected: (_) => setState(() => _department = null),
                    ),
                  ),
                  for (final name in _departments)
                    Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(name),
                        selected: _department == name,
                        onSelected: (_) => setState(() => _department = _department == name ? null : name),
                      ),
                    ),
                ],
              ),
            ),
          if (_total > _pageSize)
            _PeoplePager(
              page: _page,
              total: _total,
              pageSize: _pageSize,
              itemCount: _people.length,
              loading: _loading,
              onPrev: _hasPrev ? () => _goPage(_page - 1) : null,
              onNext: _hasNext ? () => _goPage(_page + 1) : null,
            ),
          Expanded(
            child: _loading && _people.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : _error != null && _people.isEmpty
                    ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
                    : _people.isEmpty
                        ? const Center(
                            child: Text('No people in this company', style: TextStyle(color: AppColors.textSecondary)),
                          )
                        : ListView.separated(
                            controller: _listScroll,
                            padding: const EdgeInsets.fromLTRB(16, 4, 16, 28),
                            itemCount: _groupedRows.length,
                            separatorBuilder: (_, _) => const SizedBox(height: 8),
                            itemBuilder: (context, i) {
                              final (header, user) = _groupedRows[i];
                              if (header != null) {
                                return Padding(
                                  padding: const EdgeInsets.fromLTRB(4, 8, 4, 0),
                                  child: Text(
                                    header,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w800,
                                      fontSize: 13,
                                      color: AppColors.darkBlue,
                                    ),
                                  ),
                                );
                              }
                              return _PersonCard(
                                user: user!,
                                regionCode: widget.regionCode,
                                onTap: () => _openPerson(user),
                              );
                            },
                          ),
          ),
        ],
      ),
    );
  }
}

class _PeoplePager extends StatelessWidget {
  const _PeoplePager({
    required this.page,
    required this.total,
    required this.pageSize,
    required this.itemCount,
    required this.loading,
    required this.onPrev,
    required this.onNext,
  });

  final int page;
  final int total;
  final int pageSize;
  final int itemCount;
  final bool loading;
  final VoidCallback? onPrev;
  final VoidCallback? onNext;

  @override
  Widget build(BuildContext context) {
    final from = total == 0 ? 0 : page * pageSize + 1;
    final to = page * pageSize + itemCount;
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 0, 8, 8),
      child: Row(
        children: [
          TextButton.icon(
            onPressed: loading ? null : onPrev,
            icon: Icon(PhosphorIcons.caretLeft(), size: 16),
            label: const Text('Previous'),
          ),
          Expanded(
            child: Text(
              loading ? 'Loading…' : '$from–$to of $total',
              textAlign: TextAlign.center,
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
            ),
          ),
          TextButton(
            onPressed: loading ? null : onNext,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('Next'),
                const SizedBox(width: 4),
                Icon(PhosphorIcons.caretRight(), size: 16),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _PersonCard extends StatelessWidget {
  const _PersonCard({required this.user, required this.regionCode, required this.onTap});

  final OrgUser user;
  final String regionCode;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final home = user.isHomeCompany(regionCode);
    final multi = user.regionCodes.map((c) => c.toUpperCase()).toSet().length > 1 ||
        ((user.homeRegionCode ?? '').isNotEmpty &&
            user.regionCodes.any((c) => c.toUpperCase() != (user.homeRegionCode ?? '').toUpperCase()));
    final subtitle = [
      if (user.hasAppLogin) _roleLabel(user.role, user.homeRegionCode),
      user.departmentName ?? '',
    ].where((s) => s.isNotEmpty).join(' · ');
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(14),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 12, 10, 12),
          child: Row(
            children: [
              CircleAvatar(
                radius: 20,
                backgroundColor: AppColors.lightBlue,
                child: Text(
                  _initials(user.displayName),
                  style: const TextStyle(color: AppColors.darkBlue, fontWeight: FontWeight.w800, fontSize: 13),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      user.displayName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15),
                    ),
                    if (subtitle.isNotEmpty) ...[
                      const SizedBox(height: 2),
                      Text(
                        subtitle,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    home ? 'Home' : 'Also here',
                    style: const TextStyle(
                      color: AppColors.darkBlue,
                      fontWeight: FontWeight.w700,
                      fontSize: 11,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    user.hasAppLogin
                        ? (multi ? 'Multi-region' : 'Signed in')
                        : 'ERP only',
                    style: const TextStyle(color: AppColors.textSecondary, fontSize: 10, fontWeight: FontWeight.w600),
                  ),
                ],
              ),
              const SizedBox(width: 4),
              Icon(PhosphorIcons.caretRight(), color: AppColors.textSecondary, size: 16),
            ],
          ),
        ),
      ),
    );
  }
}

class AdminPersonScreen extends ConsumerStatefulWidget {
  const AdminPersonScreen({super.key, required this.userId, required this.regionCode, this.user});

  final int userId;
  final String regionCode;
  final OrgUser? user;

  @override
  ConsumerState<AdminPersonScreen> createState() => _AdminPersonScreenState();
}

class _AdminPersonScreenState extends ConsumerState<AdminPersonScreen> {
  OrgUser? _user;
  late Set<String> _selected;
  bool _loading = true;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _user = widget.user;
    _selected = {
      for (final c in widget.user?.regionCodes ?? const <String>[]) c.toUpperCase(),
      if ((widget.user?.homeRegionCode ?? '').isNotEmpty) widget.user!.homeRegionCode!.toUpperCase(),
    };
    _loading = widget.user == null;
    _refresh();
  }

  void _applyUser(OrgUser user) {
    _user = user;
    _selected = {
      for (final c in user.regionCodes) c.toUpperCase(),
      if ((user.homeRegionCode ?? '').isNotEmpty) user.homeRegionCode!.toUpperCase(),
    };
  }

  Future<void> _refresh() async {
    try {
      final user = await ref.read(apiClientProvider).adminUser(widget.userId);
      if (!mounted) return;
      setState(() {
        _applyUser(user);
        _loading = false;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  /// Roles Admin can give (Admin itself comes from ERP). Head of Accountant is Blue Rhine
  /// Contracting's second accounts level; Finance Manager has no ERP role either.
  static const _assignableRoles = {
    'employee': 'Employee',
    'hod': 'Head of Department',
    'accountant': 'Accountant',
    'head_accountant': 'Head of Accountant',
    'finance_manager': 'Finance Manager',
  };

  Future<void> _setRole(String role) async {
    final user = _user;
    if (user == null || role == user.role) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).setUserRole(user.id, role);
      await _refresh();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Role changed to ${_assignableRoles[role] ?? role}. It applies at their next sign-in.')),
        );
      }
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _save() async {
    final user = _user;
    if (user == null) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final home = (user.homeRegionCode ?? '').toUpperCase();
      final selected = _selected.map((c) => c.toUpperCase()).toSet();
      final extras = [for (final c in selected) if (c != home) c];
      final payload = extras.isEmpty ? <String>[] : [...{if (home.isNotEmpty) home, ...extras}];
      final updated = await ref.read(apiClientProvider).setUserRegions(user.id, payload);
      if (!mounted) return;
      setState(() {
        _applyUser(updated);
        _busy = false;
      });
      if (mounted) Navigator.of(context).pop();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _busy = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = _user;
    final regions = ref.watch(adminRegionsProvider);
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: BrandAppBar(
        title: user?.displayName ?? 'Person',
        automaticallyImplyLeading: true,
        showMenuAction: false,
      ),
      body: _loading && user == null
          ? const Center(child: CircularProgressIndicator())
          : user == null
              ? Center(child: Text(_error ?? 'Person not found'))
              : regions.when(
                  loading: () => const Center(child: CircularProgressIndicator()),
                  error: (e, _) => Center(child: Text('$e')),
                  data: (list) {
                    String? homeTitle;
                    for (final r in list) {
                      if (r.regionCode.toUpperCase() == (user.homeRegionCode ?? '').toUpperCase()) {
                        homeTitle = companyTitle(r);
                        break;
                      }
                    }
                    homeTitle ??= user.homeRegionCode;
                    return ListView(
                      padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
                      children: [
                      _PersonHeader(user: user),
                      const SizedBox(height: 12),
                      ClaimDetailsCard(
                        title: 'Details',
                        rows: [
                          ClaimDetailRow(
                            label: 'Role',
                            value: _roleLabel(user.role, user.homeRegionCode).isNotEmpty ? _roleLabel(user.role, user.homeRegionCode) : '—',
                          ),
                          if ((user.erpRole ?? '').trim().isNotEmpty &&
                              (user.erpRole ?? '').trim().toLowerCase() != _roleLabel(user.role, user.homeRegionCode).toLowerCase())
                            ClaimDetailRow(label: 'ERP role', value: user.erpRole!.trim()),
                          ClaimDetailRow(
                            label: 'Department',
                            value: (user.departmentName ?? '').trim().isEmpty ? '—' : user.departmentName!.trim(),
                          ),
                          ClaimDetailRow(
                            label: 'Username',
                            value: (user.username ?? '').trim().isEmpty ? '—' : user.username!.trim(),
                          ),
                          if ((user.email ?? '').trim().isNotEmpty)
                            ClaimDetailRow(label: 'Email', value: user.email!.trim()),
                          if (user.employeeId != null) ClaimDetailRow(label: 'Employee ID', value: '${user.employeeId}'),
                          ClaimDetailRow(label: 'Home company', value: homeTitle ?? '—'),
                          ClaimDetailRow(
                            label: 'App access',
                            value: user.hasAppLogin ? 'Signed in' : 'Not signed in yet',
                          ),
                        ],
                      ),
                      if (user.hasAppLogin && user.role != 'admin') ...[
                        const SizedBox(height: 12),
                        DropdownButtonFormField<String>(
                          initialValue: _assignableRoles.containsKey(user.role) ? user.role : null,
                          decoration: const InputDecoration(
                            labelText: 'App role',
                            helperText: 'E.g. Head of Accountant or Finance Manager, which ERP has no role for.',
                          ),
                          items: [
                            for (final e in _assignableRoles.entries)
                              DropdownMenuItem(value: e.key, child: Text(e.value)),
                          ],
                          onChanged: _busy ? null : (v) => v == null ? null : _setRole(v),
                        ),
                      ],
                      const SizedBox(height: 18),
                      const Text(
                        'Companies',
                        style: TextStyle(
                          color: AppColors.textSecondary,
                          fontWeight: FontWeight.w700,
                          fontSize: 13,
                          letterSpacing: 0.2,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        user.hasAppLogin
                            ? 'Home company comes from ERP and stays on. Tick extra companies for a multi-region user — they pick one on each new bill. '
                                'For an HOD, Accountant or Finance Manager, ticked companies also decide whose bills they approve.'
                            : 'This is the ERP employee record. Extra companies can be ticked after they first sign in to the expense app — nothing is copied until then.',
                        style: const TextStyle(color: AppColors.textSecondary, height: 1.35),
                      ),
                      const SizedBox(height: 8),
                      for (final r in list)
                        _CompanyAssignTile(
                          region: r,
                          home: (user.homeRegionCode ?? '').toUpperCase(),
                          selected: _selected.contains(r.regionCode.toUpperCase()),
                          enabled: user.hasAppLogin,
                          onChanged: (v) => setState(() {
                            final code = r.regionCode.toUpperCase();
                            if (v == true) {
                              _selected.add(code);
                            } else {
                              _selected.remove(code);
                            }
                          }),
                        ),
                      if (user.hasAppLogin) ...[
                        const SizedBox(height: 16),
                        FilledButton(
                          onPressed: _busy ? null : _save,
                          child: Text(_busy ? 'Saving…' : 'Save companies'),
                        ),
                      ],
                      if (_error != null) ...[
                        const SizedBox(height: 8),
                        Text(_error!, style: const TextStyle(color: Colors.red)),
                      ],
                    ],
                  );
                  },
                ),
    );
  }
}

class _PersonHeader extends StatelessWidget {
  const _PersonHeader({required this.user});

  final OrgUser user;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(16),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 28,
              backgroundColor: AppColors.lightBlue,
              child: Text(
                _initials(user.displayName),
                style: const TextStyle(color: AppColors.darkBlue, fontWeight: FontWeight.w800, fontSize: 18),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(user.displayName, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
                  const SizedBox(height: 4),
                  Text(
                    _roleLabel(user.role, user.homeRegionCode).isNotEmpty ? _roleLabel(user.role, user.homeRegionCode) : (user.hasAppLogin ? 'Signed in' : 'ERP employee'),
                    style: const TextStyle(color: AppColors.darkBlue, fontWeight: FontWeight.w700, fontSize: 13),
                  ),
                  if ((user.departmentName ?? '').isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(user.departmentName!, style: const TextStyle(color: AppColors.textSecondary)),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CompanyAssignTile extends StatelessWidget {
  const _CompanyAssignTile({
    required this.region,
    required this.home,
    required this.selected,
    required this.onChanged,
    this.enabled = true,
  });

  final RegionConfig region;
  final String home;
  final bool selected;
  final bool enabled;
  final ValueChanged<bool?> onChanged;

  @override
  Widget build(BuildContext context) {
    final code = region.regionCode.toUpperCase();
    final isHome = code == home;
    return CheckboxListTile(
      value: selected || isHome,
      title: Text(companyTitle(region)),
      subtitle: Text(isHome ? '$code · home (ERP)' : code),
      onChanged: (!enabled || isHome) ? null : onChanged,
    );
  }
}

String _initials(String name) {
  final parts = name.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
  if (parts.isEmpty) return 'P';
  if (parts.length == 1) {
    final word = parts.first;
    return word.substring(0, word.length >= 2 ? 2 : 1).toUpperCase();
  }
  return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
}

/// Companies on the employee-advance model, where the Finance Manager is the "Accounts
/// Manager" (mirrors backend seed EMPLOYEE_PCA_REGIONS).
const _employeeAdvanceCompanies = {'KSA'};

String _roleLabel(String? role, [String? homeRegion]) => roleLabelFor(
      role,
      employeeAdvances: _employeeAdvanceCompanies.contains((homeRegion ?? '').toUpperCase()),
    );

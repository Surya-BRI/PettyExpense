import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:phosphor_icons/phosphor_icons.dart';

import '../../api/api_client.dart';
import '../../api/models.dart';
import '../../theme/app_theme.dart';
import '../../widgets/app_nav_drawer.dart';
import '../../widgets/authenticated_image.dart';
import '../../widgets/brand_app_bar.dart';
import '../../widgets/region_branding.dart';
import 'admin_providers.dart';

class AdminRegionsScreen extends ConsumerWidget {
  const AdminRegionsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(adminRegionsProvider);
    return Scaffold(
      backgroundColor: AppColors.background,
      drawer: const AppNavDrawer(),
      appBar: const BrandAppBar(title: 'Regions', automaticallyImplyLeading: true),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text('$e', textAlign: TextAlign.center),
          ),
        ),
        data: (regions) {
          if (regions.isEmpty) {
            return const Center(child: Text('No regions configured'));
          }
          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
            itemCount: regions.length + 1,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, i) {
              if (i == 0) {
                return const Padding(
                  padding: EdgeInsets.only(bottom: 4),
                  child: Text(
                    'Tap a region to change the company name or upload a new logo. The app picks it up without an update.',
                    style: TextStyle(color: AppColors.textSecondary, height: 1.35),
                  ),
                );
              }
              final r = regions[i - 1];
              return _RegionCard(
                region: r,
                onTap: () async {
                  await Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => EditRegionScreen(region: r)),
                  );
                  ref.invalidate(adminRegionsProvider);
                  ref.invalidate(regionBrandingProvider);
                },
              );
            },
          );
        },
      ),
    );
  }
}

class _RegionCard extends StatelessWidget {
  const _RegionCard({required this.region, required this.onTap});

  final RegionConfig region;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final company = region.companyName?.trim();
    final hasCompany = company != null && company.isNotEmpty;
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
              child: Image.asset(
                regionLogoAsset(region.regionCode),
                fit: BoxFit.contain,
                alignment: Alignment.center,
              ),
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
                          hasCompany ? company : region.regionName,
                          style: const TextStyle(
                            fontWeight: FontWeight.w800,
                            fontSize: 16,
                            height: 1.25,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 8,
                          runSpacing: 6,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            _RegionChip(code: region.regionCode),
                            Text(
                              region.regionName,
                              style: const TextStyle(
                                color: AppColors.textSecondary,
                                fontSize: 13,
                              ),
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

class _RegionChip extends StatelessWidget {
  const _RegionChip({required this.code});
  final String code;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.lightBlue,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        code.toUpperCase(),
        style: const TextStyle(
          color: AppColors.darkBlue,
          fontWeight: FontWeight.w700,
          fontSize: 11,
          letterSpacing: 0.4,
        ),
      ),
    );
  }
}

class EditRegionScreen extends ConsumerStatefulWidget {
  const EditRegionScreen({super.key, required this.region});
  final RegionConfig region;

  @override
  ConsumerState<EditRegionScreen> createState() => _EditRegionScreenState();
}

class _EditRegionScreenState extends ConsumerState<EditRegionScreen> {
  late final TextEditingController _name;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _name = TextEditingController(text: widget.region.companyName ?? '');
  }

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  Future<void> _saveName() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).updateRegion(widget.region.id, companyName: _name.text.trim());
      ref.invalidate(regionBrandingProvider);
      ref.invalidate(adminRegionsProvider);
      if (mounted) Navigator.of(context).pop();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pickLogo() async {
    final picked = await ImagePicker().pickImage(source: ImageSource.gallery, imageQuality: 90);
    if (picked == null) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(apiClientProvider).uploadRegionLogo(widget.region.id, File(picked.path));
      ref.invalidate(regionBrandingProvider);
      ref.invalidate(adminRegionsProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Logo updated')));
        Navigator.of(context).pop();
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final logo = widget.region.logoUrl;
    final r = widget.region;
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: BrandAppBar(
        title: r.companyName?.trim().isNotEmpty == true ? r.companyName! : r.regionName,
        automaticallyImplyLeading: true,
        showMenuAction: false,
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
        children: [
          Material(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(16),
            clipBehavior: Clip.antiAlias,
            child: Column(
              children: [
                Container(
                  height: 120,
                  width: double.infinity,
                  color: const Color(0xFFF4F6F8),
                  padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 22),
                  child: logo != null && logo.isNotEmpty
                      ? AuthenticatedImage(path: logo, fit: BoxFit.contain)
                      : Image.asset(regionLogoAsset(r.regionCode), fit: BoxFit.contain),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
                  child: Row(
                    children: [
                      _RegionChip(code: r.regionCode),
                      const SizedBox(width: 8),
                      Text(r.regionName, style: const TextStyle(color: AppColors.textSecondary)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          TextField(
            controller: _name,
            decoration: const InputDecoration(labelText: 'Company name'),
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: _busy ? null : _pickLogo,
            icon: Icon(PhosphorIcons.image()),
            label: const Text('Upload or replace logo'),
          ),
          const SizedBox(height: 10),
          FilledButton(
            onPressed: _busy ? null : _saveName,
            child: Text(_busy ? 'Saving…' : 'Save name'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
        ],
      ),
    );
  }
}

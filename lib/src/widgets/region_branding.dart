import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../api/models.dart';

/// Bundled fallback while `logoUrl` on the region row is empty, or the branding API is down.
const kDefaultRegionLogoAsset = 'assets/logos/Dubai_LOGO.png';

const kRegionLogoAssets = {
  'UAE': 'assets/logos/UAE_LOGO.png',
  'KSA': 'assets/logos/KSA_LOGO.png',
  'DUBAI': 'assets/logos/Dubai_LOGO.png',
};

String regionLogoAsset(String? regionCode) =>
    kRegionLogoAssets[(regionCode ?? '').toUpperCase()] ?? kDefaultRegionLogoAsset;

final regionBrandingProvider =
    FutureProvider.autoDispose.family<RegionConfig?, String>((ref, regionCode) async {
  final code = regionCode.trim();
  if (code.isEmpty) return null;
  final api = ref.watch(apiClientProvider);
  try {
    return await api.getBranding(code);
  } catch (_) {}
  try {
    final all = await api.listRegions();
    for (final r in all) {
      if (r.regionCode.toUpperCase() == code.toUpperCase()) return r;
    }
  } catch (_) {}
  return null;
});

/// Region company mark: uploaded `logoUrl` from `ErpExpenseRegionConfig`, else the bundled asset.
class RegionLogo extends ConsumerWidget {
  const RegionLogo({
    super.key,
    required this.regionCode,
    this.height,
    this.width,
    this.fit = BoxFit.contain,
    this.alignment = Alignment.centerLeft,
  });

  final String? regionCode;
  final double? height;
  final double? width;
  final BoxFit fit;
  final Alignment alignment;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final code = regionCode?.trim();
    if (code == null || code.isEmpty) {
      return SizedBox(height: height, width: width);
    }
    final uploaded = ref.watch(regionBrandingProvider(code)).valueOrNull?.logoUrl;
    if (uploaded != null && uploaded.trim().isNotEmpty) {
      return _UploadedRegionLogo(
        path: uploaded.trim(),
        height: height,
        width: width,
        fit: fit,
        alignment: alignment,
        fallbackCode: code,
      );
    }
    return Image.asset(
      regionLogoAsset(code),
      height: height,
      width: width,
      fit: fit,
      alignment: alignment,
    );
  }
}

class _UploadedRegionLogo extends ConsumerStatefulWidget {
  const _UploadedRegionLogo({
    required this.path,
    required this.fallbackCode,
    this.height,
    this.width,
    this.fit = BoxFit.contain,
    this.alignment = Alignment.centerLeft,
  });

  final String path;
  final String? fallbackCode;
  final double? height;
  final double? width;
  final BoxFit fit;
  final Alignment alignment;

  @override
  ConsumerState<_UploadedRegionLogo> createState() => _UploadedRegionLogoState();
}

class _UploadedRegionLogoState extends ConsumerState<_UploadedRegionLogo> {
  late Future<Uint8List> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(apiClientProvider).fetchImageBytes(widget.path);
  }

  @override
  void didUpdateWidget(_UploadedRegionLogo oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.path != widget.path) {
      _future = ref.read(apiClientProvider).fetchImageBytes(widget.path);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Uint8List>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.hasData) {
          return Image.memory(
            snapshot.data!,
            height: widget.height,
            width: widget.width,
            fit: widget.fit,
            alignment: widget.alignment,
          );
        }
        return Image.asset(
          regionLogoAsset(widget.fallbackCode),
          height: widget.height,
          width: widget.width,
          fit: widget.fit,
          alignment: widget.alignment,
        );
      },
    );
  }
}

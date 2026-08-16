import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

/// A single pulsing placeholder rectangle for loading skeletons. Deliberately
/// dependency-free (no shimmer package) — a slow opacity pulse reads as
/// "loading" just as clearly for a shape this simple.
class ShimmerBox extends StatefulWidget {
  const ShimmerBox({
    super.key,
    required this.height,
    this.width,
    this.widthFraction,
    this.borderRadius,
  });

  final double height;
  final double? width;
  final double? widthFraction;
  final BorderRadius? borderRadius;

  @override
  State<ShimmerBox> createState() => _ShimmerBoxState();
}

class _ShimmerBoxState extends State<ShimmerBox> with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _opacity;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: const Duration(milliseconds: 900))
      ..repeat(reverse: true);
    _opacity = Tween<double>(begin: 0.55, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final box = FractionallySizedBox(
      widthFactor: widget.widthFraction,
      child: Container(
        height: widget.height,
        width: widget.width,
        decoration: BoxDecoration(
          color: AppColors.divider,
          borderRadius: widget.borderRadius ?? BorderRadius.circular(6),
        ),
      ),
    );
    return AnimatedBuilder(
      animation: _opacity,
      builder: (context, child) => Opacity(opacity: _opacity.value, child: child),
      child: box,
    );
  }
}

import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

/// Standard rounded/bordered card container used across claim and approval
/// screens — extracted so every screen's cards look and behave identically.
class AppCard extends StatelessWidget {
  const AppCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.borderRadius = 16,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final double borderRadius;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(borderRadius),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(borderRadius),
          border: Border.all(color: AppColors.divider),
        ),
        padding: padding,
        child: child,
      ),
    );
  }
}

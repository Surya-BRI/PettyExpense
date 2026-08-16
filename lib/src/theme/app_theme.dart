import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Primary UI tokens (brand). Slight tints allowed for status/success.
class AppColors {
  AppColors._();

  // Brand
  static const Color orange = Color(0xFFF54900);
  static const Color darkBlue = Color(0xFF32568E);
  static const Color brightBlue = Color(0xFF155DFC);
  static const Color lightBlue = Color(0xFFE3F2FD);

  // Surfaces
  static const Color background = Color(0xFFF8F9FA);
  static const Color card = Color(0xFFFFFFFF);

  // Text
  static const Color textPrimary = Color(0xFF1A1C1E);
  static const Color textSecondary = Color(0xFF6C7278);

  // Lines
  static const Color divider = Color(0xFFE0E0E0);

  // Soft status helpers (derived / light green kept for success)
  static const Color success = Color(0xFF2E7D4F);
  static const Color successSoft = Color(0xFFE8F5E9);
  static const Color danger = Color(0xFFC62828);
  static const Color warningSoft = Color(0xFFFFF3E0);
}

class AppTheme {
  // Backward-compatible aliases used across screens
  static const Color forest = AppColors.darkBlue;
  static const Color moss = AppColors.brightBlue;
  static const Color sand = AppColors.background;
  static const Color ink = AppColors.textPrimary;
  static const Color clay = AppColors.orange;

  static ThemeData get light {
    final scheme = ColorScheme.light(
      primary: AppColors.darkBlue,
      onPrimary: Colors.white,
      secondary: AppColors.orange,
      onSecondary: Colors.white,
      tertiary: AppColors.brightBlue,
      surface: AppColors.card,
      onSurface: AppColors.textPrimary,
      surfaceContainerHighest: AppColors.lightBlue,
      outline: AppColors.divider,
      error: AppColors.danger,
    );

    const baseTextTheme = TextTheme(
      bodyLarge: TextStyle(color: AppColors.textPrimary),
      bodyMedium: TextStyle(color: AppColors.textPrimary),
      bodySmall: TextStyle(color: AppColors.textSecondary),
      titleLarge: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w700),
      titleMedium: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w600),
      titleSmall: TextStyle(color: AppColors.textSecondary),
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: AppColors.background,
      dividerColor: AppColors.divider,
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.darkBlue,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: AppColors.orange,
        foregroundColor: Colors.white,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.orange,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.brightBlue,
          side: const BorderSide(color: AppColors.brightBlue),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(foregroundColor: AppColors.brightBlue),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.card,
        labelStyle: const TextStyle(color: AppColors.textSecondary),
        hintStyle: const TextStyle(color: AppColors.textSecondary),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.divider),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.divider),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.darkBlue, width: 1.5),
        ),
      ),
      cardTheme: CardThemeData(
        color: AppColors.card,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.divider),
        ),
      ),
      bottomAppBarTheme: const BottomAppBarThemeData(
        color: AppColors.card,
        elevation: 8,
      ),
      chipTheme: ChipThemeData(
        backgroundColor: AppColors.lightBlue,
        selectedColor: AppColors.darkBlue.withValues(alpha: 0.15),
        labelStyle: const TextStyle(color: AppColors.textPrimary),
        side: const BorderSide(color: AppColors.divider),
      ),
      textTheme: GoogleFonts.interTextTheme(baseTextTheme),
    );
  }
}

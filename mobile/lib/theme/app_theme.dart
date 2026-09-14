import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppColors {
  static const bg = Color(0xFFEEF1FB);
  static const card = Color(0xFFFFFFFF);
  static const ink = Color(0xFF14161B);
  static const inkSoft = Color(0xFF6B7280);
  static const inkFaint = Color(0xFF9CA3AF);
  static const blue = Color(0xFF3358F0);
  static const blueDark = Color(0xFF1E3FC4);
  static const blueTint = Color(0xFFE7ECFD);
  static const line = Color(0xFFE7E9F5);
  static const pill = Color(0xFFEDF0FD);
  static const green = Color(0xFF16A34A);
  static const greenTint = Color(0xFFDCFCE7);
  static const amber = Color(0xFFD97706);
  static const amberTint = Color(0xFFFEF3C7);
  static const red = Color(0xFFDC2626);
  static const redTint = Color(0xFFFEE2E2);
  static const grayTint = Color(0xFFF1F2F6);
}

class AppTheme {
  static ThemeData light() {
    final base = ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: AppColors.bg,
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.blue,
        brightness: Brightness.light,
        primary: AppColors.blue,
        surface: AppColors.card,
      ),
    );

    final textTheme = GoogleFonts.interTextTheme(base.textTheme).copyWith(
      headlineMedium: GoogleFonts.inter(fontSize: 27, fontWeight: FontWeight.w800, color: AppColors.ink, letterSpacing: -0.2),
      headlineSmall: GoogleFonts.inter(fontSize: 21, fontWeight: FontWeight.w800, color: AppColors.ink),
      titleLarge: GoogleFonts.inter(fontSize: 19, fontWeight: FontWeight.w800, color: AppColors.ink),
      titleMedium: GoogleFonts.inter(fontSize: 16.5, fontWeight: FontWeight.w800, color: AppColors.ink),
      bodyMedium: GoogleFonts.inter(fontSize: 14, color: AppColors.ink),
      bodySmall: GoogleFonts.inter(fontSize: 12.5, color: AppColors.inkSoft),
      labelLarge: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w700),
    );

    return base.copyWith(
      textTheme: textTheme,
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.bg,
        elevation: 0,
        foregroundColor: AppColors.ink,
        titleTextStyle: textTheme.headlineMedium,
      ),
      cardTheme: CardThemeData(
        color: AppColors.card,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.line),
        ),
        margin: EdgeInsets.zero,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.blue,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: textTheme.labelLarge,
          elevation: 0,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.ink,
          side: const BorderSide(color: AppColors.line),
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 18),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(foregroundColor: AppColors.blue, textStyle: textTheme.labelLarge),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.grayTint,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
        contentPadding: const EdgeInsets.symmetric(horizontal: 13, vertical: 12),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: Colors.white,
        selectedItemColor: AppColors.blue,
        unselectedItemColor: AppColors.inkFaint,
        showUnselectedLabels: true,
        type: BottomNavigationBarType.fixed,
      ),
    );
  }
}

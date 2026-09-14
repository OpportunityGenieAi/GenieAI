import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';

import 'l10n/app_strings.dart';
import 'providers/app_providers.dart';
import 'providers/auth_provider.dart';
import 'screens/splash_screen.dart';
import 'theme/app_theme.dart';

class OpportunityGenieApp extends StatelessWidget {
  const OpportunityGenieApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => ScholarshipProvider()),
        ChangeNotifierProvider(create: (_) => ProfileProvider()),
        ChangeNotifierProvider(create: (_) => TrackerProvider()),
      ],
      child: MaterialApp(
        title: 'OpportunityGenie AI',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        supportedLocales: AppStrings.supportedLocales,
        localizationsDelegates: const [
          AppStringsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        home: const SplashScreen(),
      ),
    );
  }
}

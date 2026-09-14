import 'package:flutter/material.dart';

/// A deliberately simple localization approach: a Map per locale instead
/// of ARB codegen, so it works without running `flutter gen-l10n` first.
/// Add more locales by adding another map below and registering the
/// locale in main.dart's supportedLocales.
class AppStrings {
  static const Map<String, Map<String, String>> _values = {
    'en': {
      'find_your_scholarship': 'Find Your Scholarship',
      'explore_scholarships': 'Explore Scholarships',
      'create_free_account': 'Create a free account',
      'unlock_features': 'Unlock Match scores, Tracker, Advisor & more',
      'latest_scholarships': 'Latest Scholarships',
      'search_hint': 'Search scholarships, countries…',
      'home': 'Home',
      'match': 'Match',
      'tracker': 'Tracker',
      'advisor': 'Advisor',
      'profile': 'Profile',
      'apply_official': 'Apply on official site',
      'log_in': 'Log in',
      'create_account': 'Create account',
    },
    'es': {
      'find_your_scholarship': 'Encuentra Tu Beca',
      'explore_scholarships': 'Explorar Becas',
      'create_free_account': 'Crea una cuenta gratis',
      'unlock_features': 'Desbloquea Coincidencias, Seguimiento, Asesor y más',
      'latest_scholarships': 'Últimas Becas',
      'search_hint': 'Buscar becas, países…',
      'home': 'Inicio',
      'match': 'Match',
      'tracker': 'Seguimiento',
      'advisor': 'Asesor',
      'profile': 'Perfil',
      'apply_official': 'Solicitar en el sitio oficial',
      'log_in': 'Iniciar sesión',
      'create_account': 'Crear cuenta',
    },
    'fr': {
      'find_your_scholarship': 'Trouvez Votre Bourse',
      'explore_scholarships': 'Explorer les Bourses',
      'create_free_account': 'Créer un compte gratuit',
      'unlock_features': 'Débloquez Correspondances, Suivi, Conseiller et plus',
      'latest_scholarships': 'Dernières Bourses',
      'search_hint': 'Rechercher des bourses, pays…',
      'home': 'Accueil',
      'match': 'Match',
      'tracker': 'Suivi',
      'advisor': 'Conseiller',
      'profile': 'Profil',
      'apply_official': 'Postuler sur le site officiel',
      'log_in': 'Se connecter',
      'create_account': 'Créer un compte',
    },
  };

  final Locale locale;
  AppStrings(this.locale);

  static AppStrings of(BuildContext context) {
    return Localizations.of<AppStrings>(context, AppStrings) ?? AppStrings(const Locale('en'));
  }

  String t(String key) {
    final lang = _values.containsKey(locale.languageCode) ? locale.languageCode : 'en';
    return _values[lang]?[key] ?? _values['en']![key] ?? key;
  }

  static const supportedLocales = [Locale('en'), Locale('es'), Locale('fr')];
}

class AppStringsDelegate extends LocalizationsDelegate<AppStrings> {
  const AppStringsDelegate();

  @override
  bool isSupported(Locale locale) =>
      AppStrings.supportedLocales.map((l) => l.languageCode).contains(locale.languageCode);

  @override
  Future<AppStrings> load(Locale locale) async => AppStrings(locale);

  @override
  bool shouldReload(AppStringsDelegate old) => false;
}

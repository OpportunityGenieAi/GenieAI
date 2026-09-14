/// API base URL, overridable at build/run time:
///   flutter run --dart-define=API_BASE_URL=https://api.yourdomain.com
///   flutter build apk --dart-define=API_BASE_URL=https://api.yourdomain.com
///
/// Defaults to a local backend for development.
/// - Android emulator reaches the host machine via 10.0.2.2, not localhost.
/// - iOS simulator can use localhost directly.
class Env {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
}

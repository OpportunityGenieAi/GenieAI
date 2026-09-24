import 'package:flutter/foundation.dart';

import '../models/user.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../services/secure_storage_service.dart';

/// ok = logged in; unverified = right password but email not confirmed yet.
enum LoginResult { ok, unverified, error }

class AuthProvider extends ChangeNotifier {
  final _authService = AuthService();

  AppUser? _user;
  bool _loading = true;
  String? _error;

  AppUser? get user => _user;
  bool get isLoggedIn => _user != null;
  bool get loading => _loading;
  String? get error => _error;

  Future<void> tryRestoreSession() async {
    _loading = true;
    notifyListeners();
    final token = await SecureStorageService.readToken();
    if (token != null) {
      _user = await _authService.fetchCurrentUser();
    }
    _loading = false;
    notifyListeners();
  }

  Future<LoginResult> login(String email, String password) async {
    _error = null;
    try {
      _user = await _authService.login(email: email, password: password);
      notifyListeners();
      return LoginResult.ok;
    } on ApiException catch (e) {
      // 403 = correct password but email not verified yet
      if (e.statusCode == 403) return LoginResult.unverified;
      _error = e.message;
      notifyListeners();
      return LoginResult.error;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return LoginResult.error;
    }
  }

  /// Returns true when the confirmation code email has been sent.
  Future<bool> signup({
    required String name,
    required String email,
    required String password,
  }) async {
    _error = null;
    try {
      await _authService.signup(name: name, email: email, password: password);
      return true;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  /// Confirms the emailed code and logs the user in.
  Future<bool> verifyEmail(String email, String code) async {
    _error = null;
    try {
      _user = await _authService.verifyEmail(email: email, code: code);
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    await _authService.logout();
    _user = null;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}

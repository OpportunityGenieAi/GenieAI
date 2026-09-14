import 'package:flutter/foundation.dart';

import '../models/user.dart';
import '../services/auth_service.dart';
import '../services/secure_storage_service.dart';

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

  Future<bool> login(String email, String password) async {
    _error = null;
    try {
      _user = await _authService.login(email: email, password: password);
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> signup({
    required String name,
    required String email,
    required String password,
    required String securityQuestion,
    required String securityAnswer,
  }) async {
    _error = null;
    try {
      _user = await _authService.signup(
        name: name,
        email: email,
        password: password,
        securityQuestion: securityQuestion,
        securityAnswer: securityAnswer,
      );
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

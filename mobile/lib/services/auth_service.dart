import '../models/user.dart';
import 'api_client.dart';
import 'secure_storage_service.dart';

class AuthService {
  /// Step 1: creates the account and emails a confirmation code. Does NOT log in.
  Future<void> signup({
    required String name,
    required String email,
    required String password,
  }) async {
    await apiClient.post('/auth/signup', body: {
      'name': name,
      'email': email,
      'password': password,
    });
  }

  /// Step 2: the user types the emailed code; on success they're logged in.
  Future<AppUser> verifyEmail({required String email, required String code}) async {
    final res = await apiClient.post('/auth/verify-email', body: {'email': email, 'code': code});
    await SecureStorageService.saveToken(res['access_token'] as String);
    return AppUser.fromJson(res['user'] as Map<String, dynamic>);
  }

  Future<void> resendCode(String email) async {
    await apiClient.post('/auth/resend-code', body: {'email': email});
  }

  Future<AppUser> login({required String email, required String password}) async {
    final res = await apiClient.post('/auth/login', body: {'email': email, 'password': password});
    await SecureStorageService.saveToken(res['access_token'] as String);
    return AppUser.fromJson(res['user'] as Map<String, dynamic>);
  }

  /// Emails a password-reset code.
  Future<void> forgotPasswordStart(String email) async {
    await apiClient.post('/auth/forgot-password/start', body: {'email': email});
  }

  Future<void> forgotPasswordVerify({
    required String email,
    required String code,
    required String newPassword,
  }) async {
    await apiClient.post('/auth/forgot-password/verify', body: {
      'email': email,
      'code': code,
      'new_password': newPassword,
    });
  }

  Future<AppUser?> fetchCurrentUser() async {
    try {
      final res = await apiClient.get('/auth/me', auth: true);
      return AppUser.fromJson(res as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<void> logout() => SecureStorageService.clearToken();
}

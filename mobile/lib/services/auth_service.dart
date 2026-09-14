import '../models/user.dart';
import 'api_client.dart';
import 'secure_storage_service.dart';

class AuthService {
  Future<AppUser> signup({
    required String name,
    required String email,
    required String password,
    required String securityQuestion,
    required String securityAnswer,
  }) async {
    final res = await apiClient.post('/auth/signup', body: {
      'name': name,
      'email': email,
      'password': password,
      'security_question': securityQuestion,
      'security_answer': securityAnswer,
    });
    await SecureStorageService.saveToken(res['access_token'] as String);
    return AppUser.fromJson(res['user'] as Map<String, dynamic>);
  }

  Future<AppUser> login({required String email, required String password}) async {
    final res = await apiClient.post('/auth/login', body: {'email': email, 'password': password});
    await SecureStorageService.saveToken(res['access_token'] as String);
    return AppUser.fromJson(res['user'] as Map<String, dynamic>);
  }

  Future<String> forgotPasswordStart(String email) async {
    final res = await apiClient.post('/auth/forgot-password/start', body: {'email': email});
    return res['security_question'] as String;
  }

  Future<void> forgotPasswordVerify({
    required String email,
    required String securityAnswer,
    required String newPassword,
  }) async {
    await apiClient.post('/auth/forgot-password/verify', body: {
      'email': email,
      'security_answer': securityAnswer,
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

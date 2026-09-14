import 'dart:convert';
import 'package:http/http.dart' as http;

import '../config/env.dart';
import 'secure_storage_service.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);
  @override
  String toString() => message;
}

class ApiClient {
  final String baseUrl;
  ApiClient({this.baseUrl = Env.apiBaseUrl});

  Future<Map<String, String>> _headers({bool auth = false}) async {
    final headers = {'Content-Type': 'application/json'};
    if (auth) {
      final token = await SecureStorageService.readToken();
      if (token != null) headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  dynamic _decode(http.Response res) {
    final body = res.body.isNotEmpty ? jsonDecode(res.body) : null;
    if (res.statusCode >= 200 && res.statusCode < 300) return body;
    final detail = (body is Map && body['detail'] != null) ? body['detail'].toString() : 'Something went wrong (${res.statusCode}).';
    throw ApiException(res.statusCode, detail);
  }

  Future<dynamic> get(String path, {bool auth = false, Map<String, String>? query}) async {
    final uri = Uri.parse('$baseUrl$path').replace(queryParameters: query);
    final res = await http.get(uri, headers: await _headers(auth: auth));
    return _decode(res);
  }

  Future<dynamic> post(String path, {Map<String, dynamic>? body, bool auth = false}) async {
    final uri = Uri.parse('$baseUrl$path');
    final res = await http.post(uri, headers: await _headers(auth: auth), body: body != null ? jsonEncode(body) : null);
    return _decode(res);
  }

  Future<dynamic> put(String path, {Map<String, dynamic>? body, bool auth = false}) async {
    final uri = Uri.parse('$baseUrl$path');
    final res = await http.put(uri, headers: await _headers(auth: auth), body: body != null ? jsonEncode(body) : null);
    return _decode(res);
  }

  Future<dynamic> patch(String path, {Map<String, dynamic>? body, bool auth = false}) async {
    final uri = Uri.parse('$baseUrl$path');
    final res = await http.patch(uri, headers: await _headers(auth: auth), body: body != null ? jsonEncode(body) : null);
    return _decode(res);
  }

  Future<void> delete(String path, {bool auth = false}) async {
    final uri = Uri.parse('$baseUrl$path');
    final res = await http.delete(uri, headers: await _headers(auth: auth));
    if (res.statusCode >= 200 && res.statusCode < 300) return;
    _decode(res);
  }
}

final apiClient = ApiClient();

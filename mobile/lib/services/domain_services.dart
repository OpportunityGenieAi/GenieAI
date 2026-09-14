import '../models/profile_models.dart';
import '../models/scholarship.dart';
import 'api_client.dart';

class ScholarshipService {
  Future<List<Scholarship>> list({String? q, String? region, bool auth = false}) async {
    final query = <String, String>{};
    if (q != null && q.isNotEmpty) query['q'] = q;
    if (region != null && region != 'All') query['region'] = region;
    final res = await apiClient.get('/scholarships', query: query, auth: auth);
    return (res as List).map((e) => Scholarship.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Scholarship> create(Scholarship s) async {
    final res = await apiClient.post('/scholarships', body: s.toJson(), auth: true);
    return Scholarship.fromJson(res as Map<String, dynamic>);
  }

  Future<Scholarship> update(String id, Scholarship s) async {
    final res = await apiClient.put('/scholarships/$id', body: s.toJson(), auth: true);
    return Scholarship.fromJson(res as Map<String, dynamic>);
  }

  Future<void> delete(String id) => apiClient.delete('/scholarships/$id', auth: true);
}

class ProfileService {
  Future<List<GradingSystem>> gpaSystems() async {
    final res = await apiClient.get('/profile/gpa/systems');
    return (res as List).map((e) => GradingSystem.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Map<String, dynamic>> convertGpa({required String systemId, required String value}) async {
    return await apiClient.post('/profile/gpa/convert', body: {'system_id': systemId, 'value': value}) as Map<String, dynamic>;
  }

  Future<GpaProfile> saveGpa({required String systemId, required String value}) async {
    final res = await apiClient.post('/profile/gpa', body: {'system_id': systemId, 'value': value}, auth: true);
    return GpaProfile.fromJson(res as Map<String, dynamic>);
  }

  Future<GpaProfile?> getGpa() async {
    final res = await apiClient.get('/profile/gpa', auth: true);
    return res == null ? null : GpaProfile.fromJson(res as Map<String, dynamic>);
  }

  Future<AcademicProfile> saveAcademic(AcademicProfile profile) async {
    final res = await apiClient.post('/profile/academic', body: profile.toJson(), auth: true);
    return AcademicProfile.fromJson(res as Map<String, dynamic>);
  }

  Future<AcademicProfile?> getAcademic() async {
    final res = await apiClient.get('/profile/academic', auth: true);
    return res == null ? null : AcademicProfile.fromJson(res as Map<String, dynamic>);
  }

  Future<Readiness?> getReadiness() async {
    final res = await apiClient.get('/profile/readiness', auth: true);
    return res == null ? null : Readiness.fromJson(res as Map<String, dynamic>);
  }
}

class TrackerService {
  Future<List<TrackerEntry>> list() async {
    final res = await apiClient.get('/tracker', auth: true);
    return (res as List).map((e) => TrackerEntry.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<void> add(String scholarshipId) => apiClient.post('/tracker/$scholarshipId', auth: true);

  Future<void> updateStatus(String scholarshipId, String status) =>
      apiClient.patch('/tracker/$scholarshipId', body: {'status': status}, auth: true);

  Future<void> remove(String scholarshipId) => apiClient.delete('/tracker/$scholarshipId', auth: true);
}

class AdvisorService {
  Future<String> getRecommendation() async {
    final res = await apiClient.post('/advisor/recommend', auth: true);
    return res['text'] as String;
  }
}

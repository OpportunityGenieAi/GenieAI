import 'package:flutter/foundation.dart';

import '../models/profile_models.dart';
import '../models/scholarship.dart';
import '../services/domain_services.dart';

class ScholarshipProvider extends ChangeNotifier {
  final _service = ScholarshipService();

  List<Scholarship> items = [];
  bool loading = false;
  String query = '';
  String region = 'All';

  Future<void> fetch({bool auth = false}) async {
    loading = true;
    notifyListeners();
    try {
      items = await _service.list(q: query, region: region, auth: auth);
    } catch (_) {
      // Keep prior items on failure; the UI can show a retry affordance.
    }
    loading = false;
    notifyListeners();
  }

  void setQuery(String q) {
    query = q;
    notifyListeners();
  }

  void setRegion(String r) {
    region = r;
    notifyListeners();
  }

  List<Scholarship> get sortedByMatch {
    final copy = [...items];
    copy.sort((a, b) => (b.matchScore ?? -1).compareTo(a.matchScore ?? -1));
    return copy;
  }
}

class ProfileProvider extends ChangeNotifier {
  final _service = ProfileService();

  GpaProfile? gpaProfile;
  AcademicProfile? academicProfile;
  Readiness? readiness;
  List<GradingSystem> systems = [];
  bool loading = false;

  bool get isComplete => gpaProfile != null && academicProfile != null;

  Future<void> loadAll() async {
    loading = true;
    notifyListeners();
    try {
      systems = await _service.gpaSystems();
      gpaProfile = await _service.getGpa();
      academicProfile = await _service.getAcademic();
      readiness = await _service.getReadiness();
    } catch (_) {}
    loading = false;
    notifyListeners();
  }

  Future<Map<String, dynamic>> previewConversion(String systemId, String value) =>
      _service.convertGpa(systemId: systemId, value: value);

  Future<void> saveGpa(String systemId, String value) async {
    gpaProfile = await _service.saveGpa(systemId: systemId, value: value);
    readiness = await _service.getReadiness();
    notifyListeners();
  }

  Future<void> saveAcademic(AcademicProfile profile) async {
    academicProfile = await _service.saveAcademic(profile);
    readiness = await _service.getReadiness();
    notifyListeners();
  }

  void reset() {
    gpaProfile = null;
    academicProfile = null;
    readiness = null;
    notifyListeners();
  }
}

class TrackerProvider extends ChangeNotifier {
  final _service = TrackerService();
  List<TrackerEntry> entries = [];
  bool loading = false;

  bool isTracked(String scholarshipId) => entries.any((e) => e.scholarshipId == scholarshipId);

  Future<void> fetch() async {
    loading = true;
    notifyListeners();
    try {
      entries = await _service.list();
    } catch (_) {}
    loading = false;
    notifyListeners();
  }

  Future<void> toggle(String scholarshipId) async {
    if (isTracked(scholarshipId)) {
      await _service.remove(scholarshipId);
    } else {
      await _service.add(scholarshipId);
    }
    await fetch();
  }

  Future<void> updateStatus(String scholarshipId, String status) async {
    await _service.updateStatus(scholarshipId, status);
    await fetch();
  }

  void reset() {
    entries = [];
    notifyListeners();
  }
}

class GradingSystem {
  final String id;
  final String label;
  final String inputType; // percent | number | select
  final double min;
  final double max;
  final List<String>? options;

  GradingSystem({
    required this.id,
    required this.label,
    required this.inputType,
    required this.min,
    required this.max,
    this.options,
  });

  factory GradingSystem.fromJson(Map<String, dynamic> json) => GradingSystem(
        id: json['id'] as String,
        label: json['label'] as String,
        inputType: json['input_type'] as String,
        min: (json['min'] as num?)?.toDouble() ?? 0,
        max: (json['max'] as num?)?.toDouble() ?? 100,
        options: (json['options'] as List?)?.map((e) => e.toString()).toList(),
      );
}

class GpaProfile {
  final double gpa;
  final double percent;
  final String ects;
  final String systemId;
  final String systemLabel;

  GpaProfile({
    required this.gpa,
    required this.percent,
    required this.ects,
    required this.systemId,
    required this.systemLabel,
  });

  factory GpaProfile.fromJson(Map<String, dynamic> json) => GpaProfile(
        gpa: (json['gpa'] as num).toDouble(),
        percent: (json['percent'] as num).toDouble(),
        ects: json['ects'] as String,
        systemId: json['system_id'] as String,
        systemLabel: json['system_label'] as String,
      );
}

class AcademicProfile {
  String level;
  String field;
  String nationality;
  double? ielts;
  int workYears;
  int publications;
  String leadership; // None | Some | Extensive
  String volunteering; // None | Occasional | Regular
  bool hasCv;
  bool hasSop;
  bool hasRecommendationLetters;

  AcademicProfile({
    this.level = "Master's",
    this.field = '',
    this.nationality = '',
    this.ielts,
    this.workYears = 0,
    this.publications = 0,
    this.leadership = 'None',
    this.volunteering = 'None',
    this.hasCv = false,
    this.hasSop = false,
    this.hasRecommendationLetters = false,
  });

  factory AcademicProfile.fromJson(Map<String, dynamic> json) => AcademicProfile(
        level: json['level'] as String? ?? "Master's",
        field: json['field'] as String? ?? '',
        nationality: json['nationality'] as String? ?? '',
        ielts: (json['ielts'] as num?)?.toDouble(),
        workYears: json['work_years'] as int? ?? 0,
        publications: json['publications'] as int? ?? 0,
        leadership: json['leadership'] as String? ?? 'None',
        volunteering: json['volunteering'] as String? ?? 'None',
        hasCv: json['has_cv'] as bool? ?? false,
        hasSop: json['has_sop'] as bool? ?? false,
        hasRecommendationLetters: json['has_recommendation_letters'] as bool? ?? false,
      );

  Map<String, dynamic> toJson() => {
        'level': level,
        'field': field,
        'nationality': nationality,
        'ielts': ielts,
        'work_years': workYears,
        'publications': publications,
        'leadership': leadership,
        'volunteering': volunteering,
        'has_cv': hasCv,
        'has_sop': hasSop,
        'has_recommendation_letters': hasRecommendationLetters,
      };
}

class ReadinessCategory {
  final String label;
  final int stars;
  ReadinessCategory({required this.label, required this.stars});

  factory ReadinessCategory.fromJson(Map<String, dynamic> json) =>
      ReadinessCategory(label: json['label'] as String, stars: json['stars'] as int);
}

class Readiness {
  final int overall;
  final List<ReadinessCategory> categories;
  Readiness({required this.overall, required this.categories});

  factory Readiness.fromJson(Map<String, dynamic> json) => Readiness(
        overall: json['overall'] as int,
        categories: (json['categories'] as List)
            .map((e) => ReadinessCategory.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class TrackerEntry {
  final String scholarshipId;
  String status; // saved | applied | interview | accepted | rejected
  final Scholarship scholarship;

  TrackerEntry({required this.scholarshipId, required this.status, required this.scholarship});

  factory TrackerEntry.fromJson(Map<String, dynamic> json) => TrackerEntry(
        scholarshipId: json['scholarship_id'] as String,
        status: json['status'] as String,
        scholarship: Scholarship.fromJson(json['scholarship'] as Map<String, dynamic>),
      );
}

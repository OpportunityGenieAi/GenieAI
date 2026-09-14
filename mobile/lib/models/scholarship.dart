class Scholarship {
  final String id;
  final String name;
  final String provider;
  final String country;
  final String level;
  final String field;
  final String funding;
  final String deadlineWindow;
  final String officialLink;
  final List<String> tags;
  final String blurb;
  final int? matchScore;
  final String? matchTier;

  Scholarship({
    required this.id,
    required this.name,
    required this.provider,
    required this.country,
    required this.level,
    required this.field,
    required this.funding,
    required this.deadlineWindow,
    required this.officialLink,
    required this.tags,
    required this.blurb,
    this.matchScore,
    this.matchTier,
  });

  factory Scholarship.fromJson(Map<String, dynamic> json) => Scholarship(
        id: json['id'] as String,
        name: json['name'] as String,
        provider: json['provider'] as String,
        country: json['country'] as String,
        level: json['level'] as String,
        field: json['field'] as String? ?? 'All fields',
        funding: json['funding'] as String? ?? 'Fully-funded',
        deadlineWindow: json['deadline_window'] as String,
        officialLink: json['official_link'] as String,
        tags: (json['tags'] as List?)?.map((e) => e.toString()).toList() ?? [],
        blurb: json['blurb'] as String? ?? '',
        matchScore: json['match_score'] as int?,
        matchTier: json['match_tier'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'name': name,
        'provider': provider,
        'country': country,
        'level': level,
        'field': field,
        'funding': funding,
        'deadline_window': deadlineWindow,
        'official_link': officialLink,
        'tags': tags,
        'blurb': blurb,
      };
}

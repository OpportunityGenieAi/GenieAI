class AppUser {
  final String id;
  final String name;
  final String email;
  final bool isAdmin;
  final String subscriptionTier;
  final String preferredLocale;

  AppUser({
    required this.id,
    required this.name,
    required this.email,
    required this.isAdmin,
    required this.subscriptionTier,
    required this.preferredLocale,
  });

  factory AppUser.fromJson(Map<String, dynamic> json) => AppUser(
        id: json['id'] as String,
        name: json['name'] as String,
        email: json['email'] as String,
        isAdmin: json['is_admin'] as bool? ?? false,
        subscriptionTier: json['subscription_tier'] as String? ?? 'free',
        preferredLocale: json['preferred_locale'] as String? ?? 'en',
      );
}

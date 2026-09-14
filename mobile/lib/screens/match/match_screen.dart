import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/app_providers.dart';
import '../../providers/auth_provider.dart';
import '../../theme/app_theme.dart';
import '../../widgets/feature_gate.dart';
import '../../widgets/scholarship_card.dart';

class MatchScreen extends StatefulWidget {
  const MatchScreen({super.key});
  @override
  State<MatchScreen> createState() => _MatchScreenState();
}

class _MatchScreenState extends State<MatchScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (context.read<AuthProvider>().isLoggedIn) {
        context.read<ScholarshipProvider>().fetch(auth: true);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    if (!auth.isLoggedIn) {
      return const FeatureGate(
        title: 'Unlock Match scores',
        body: 'See a live match percentage on every scholarship, based on your real GPA and profile.',
      );
    }

    final profile = context.watch<ProfileProvider>();
    final scholarships = context.watch<ScholarshipProvider>();
    final tracker = context.watch<TrackerProvider>();

    if (!profile.isComplete) {
      return SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Best Matches', style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(border: Border.all(color: AppColors.line, width: 1), borderRadius: BorderRadius.circular(12)),
                child: const Text(
                  'Complete your profile (GPA + academic details) on the Profile tab to see match scores here.',
                  style: TextStyle(color: AppColors.inkSoft, fontSize: 13.5),
                ),
              ),
            ],
          ),
        ),
      );
    }

    final ranked = scholarships.sortedByMatch;

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 100),
        children: [
          Text('Best Matches', style: Theme.of(context).textTheme.headlineMedium),
          Text('Ranked by fit to your saved profile', style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 16),
          ...ranked.map((s) => ScholarshipCard(
                scholarship: s,
                showMatch: true,
                isBookmarked: tracker.isTracked(s.id),
                onToggleBookmark: () => tracker.toggle(s.id),
              )),
        ],
      ),
    );
  }
}

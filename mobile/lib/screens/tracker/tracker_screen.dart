import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/app_providers.dart';
import '../../providers/auth_provider.dart';
import '../../theme/app_theme.dart';
import '../../widgets/feature_gate.dart';

class TrackerScreen extends StatefulWidget {
  const TrackerScreen({super.key});
  @override
  State<TrackerScreen> createState() => _TrackerScreenState();
}

class _TrackerScreenState extends State<TrackerScreen> {
  static const _statuses = ['saved', 'applied', 'interview', 'accepted', 'rejected'];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (context.read<AuthProvider>().isLoggedIn) {
        context.read<TrackerProvider>().fetch();
      }
    });
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'applied': return AppColors.blue;
      case 'interview': return AppColors.amber;
      case 'accepted': return AppColors.green;
      case 'rejected': return AppColors.red;
      default: return AppColors.inkSoft;
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    if (!auth.isLoggedIn) {
      return const FeatureGate(
        title: 'Unlock the Tracker',
        body: 'Save scholarships and follow your application status from saved to accepted.',
      );
    }

    final tracker = context.watch<TrackerProvider>();

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: () => tracker.fetch(),
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 100),
          children: [
            Text('Your applications', style: Theme.of(context).textTheme.bodySmall),
            Text('Tracker', style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 18),
            if (tracker.loading)
              const Padding(padding: EdgeInsets.symmetric(vertical: 40), child: Center(child: CircularProgressIndicator()))
            else if (tracker.entries.isEmpty)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(12)),
                child: const Text(
                  'Nothing saved yet. Tap the bookmark icon on any scholarship from Home to track it here.',
                  style: TextStyle(color: AppColors.inkSoft, fontSize: 13.5),
                ),
              )
            else
              ...tracker.entries.map((entry) => Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(14), border: Border.all(color: AppColors.line)),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(entry.scholarship.name, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontSize: 14.5)),
                              const SizedBox(height: 2),
                              Text('${entry.scholarship.provider} · ${entry.scholarship.deadlineWindow}', style: const TextStyle(fontSize: 12, color: AppColors.inkSoft)),
                            ],
                          ),
                        ),
                        DropdownButton<String>(
                          value: entry.status,
                          underline: const SizedBox(),
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: _statusColor(entry.status)),
                          items: _statuses
                              .map((s) => DropdownMenuItem(value: s, child: Text(s[0].toUpperCase() + s.substring(1))))
                              .toList(),
                          onChanged: (v) {
                            if (v != null) tracker.updateStatus(entry.scholarshipId, v);
                          },
                        ),
                      ],
                    ),
                  )),
          ],
        ),
      ),
    );
  }
}

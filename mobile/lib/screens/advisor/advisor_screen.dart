import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/app_providers.dart';
import '../../providers/auth_provider.dart';
import '../../services/domain_services.dart';
import '../../theme/app_theme.dart';
import '../../widgets/feature_gate.dart';

class AdvisorScreen extends StatefulWidget {
  const AdvisorScreen({super.key});
  @override
  State<AdvisorScreen> createState() => _AdvisorScreenState();
}

class _AdvisorScreenState extends State<AdvisorScreen> {
  final _advisorService = AdvisorService();
  bool _loading = false;
  String? _text;
  String? _error;

  Future<void> _ask() async {
    setState(() { _loading = true; _error = null; _text = null; });
    try {
      final result = await _advisorService.getRecommendation();
      setState(() => _text = result);
    } catch (e) {
      setState(() => _error = "Couldn't reach the AI advisor just now — try again in a moment.");
    }
    setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    if (!auth.isLoggedIn) {
      return const FeatureGate(
        title: 'Unlock the AI Advisor',
        body: 'Get a personalized, honest read on your competitiveness and concrete next steps.',
      );
    }

    final profile = context.watch<ProfileProvider>();

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 100),
        children: [
          Text('Ask anything', style: Theme.of(context).textTheme.bodySmall),
          Text('AI Advisor', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(16), border: Border.all(color: AppColors.line)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Personalized recommendations', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontSize: 15.5)),
                const SizedBox(height: 3),
                const Text('A short, honest read on your competitiveness and what would move the needle most.',
                    style: TextStyle(fontSize: 12.5, color: AppColors.inkSoft)),
                const SizedBox(height: 14),
                if (!profile.isComplete)
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(10)),
                    child: const Text('Complete your profile first — the advisor needs your GPA and academic details.',
                        style: TextStyle(fontSize: 13, color: AppColors.inkSoft)),
                  )
                else ...[
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _loading ? null : _ask,
                      child: _loading
                          ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Text('Get my recommendations'),
                    ),
                  ),
                  if (_error != null) ...[
                    const SizedBox(height: 10),
                    Text(_error!, style: const TextStyle(color: AppColors.red, fontSize: 12.5)),
                  ],
                  if (_text != null) ...[
                    const SizedBox(height: 14),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(color: AppColors.blueTint, borderRadius: BorderRadius.circular(12)),
                      child: Text(_text!, style: const TextStyle(fontSize: 13.5, color: AppColors.blueDark, height: 1.5)),
                    ),
                  ],
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

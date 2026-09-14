import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/profile_models.dart';
import '../../providers/app_providers.dart';
import '../../providers/auth_provider.dart';
import '../../theme/app_theme.dart';
import '../../widgets/feature_gate.dart';
import '../admin/admin_screen.dart';
import 'gpa_converter_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});
  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _fieldController = TextEditingController();
  final _nationalityController = TextEditingController();
  final _ieltsController = TextEditingController();
  final _workYearsController = TextEditingController(text: '0');
  final _publicationsController = TextEditingController(text: '0');
  String _level = "Master's";
  String _leadership = 'None';
  String _volunteering = 'None';
  bool _hasCv = false, _hasSop = false, _hasRecs = false;
  bool _initialized = false;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final auth = context.read<AuthProvider>();
      if (!auth.isLoggedIn) return;
      final profile = context.read<ProfileProvider>();
      await profile.loadAll();
      final ap = profile.academicProfile;
      if (ap != null) {
        setState(() {
          _level = ap.level;
          _fieldController.text = ap.field;
          _nationalityController.text = ap.nationality;
          _ieltsController.text = ap.ielts?.toString() ?? '';
          _workYearsController.text = ap.workYears.toString();
          _publicationsController.text = ap.publications.toString();
          _leadership = ap.leadership;
          _volunteering = ap.volunteering;
          _hasCv = ap.hasCv; _hasSop = ap.hasSop; _hasRecs = ap.hasRecommendationLetters;
        });
      }
      setState(() => _initialized = true);
    });
  }

  Future<void> _saveProfile() async {
    setState(() => _saving = true);
    final ap = AcademicProfile(
      level: _level,
      field: _fieldController.text.trim(),
      nationality: _nationalityController.text.trim(),
      ielts: double.tryParse(_ieltsController.text),
      workYears: int.tryParse(_workYearsController.text) ?? 0,
      publications: int.tryParse(_publicationsController.text) ?? 0,
      leadership: _leadership,
      volunteering: _volunteering,
      hasCv: _hasCv, hasSop: _hasSop, hasRecommendationLetters: _hasRecs,
    );
    try {
      await context.read<ProfileProvider>().saveAcademic(ap);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Profile saved.')));
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Could not save — try again.')));
    }
    setState(() => _saving = false);
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    if (!auth.isLoggedIn) {
      return const FeatureGate(
        title: 'Create your profile',
        body: 'Save your GPA and academic details to power match scores and the AI advisor.',
      );
    }

    final profile = context.watch<ProfileProvider>();
    final user = auth.user!;

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 100),
        children: [
          Text('Your account', style: Theme.of(context).textTheme.bodySmall),
          Text('Profile', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 18),

          _card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  CircleAvatar(radius: 26, backgroundColor: AppColors.blue,
                      child: Text(user.name.substring(0, 1).toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 19))),
                  const SizedBox(width: 12),
                  Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(user.name, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                    Text(user.email, style: const TextStyle(fontSize: 12.5, color: AppColors.inkSoft)),
                  ]),
                ]),
                const SizedBox(height: 14),
                Row(children: [
                  if (user.isAdmin)
                    Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: OutlinedButton(
                        onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const AdminScreen())),
                        child: const Text('Admin console'),
                      ),
                    ),
                  TextButton(
                    onPressed: () {
                      context.read<AuthProvider>().logout();
                      context.read<ProfileProvider>().reset();
                      context.read<TrackerProvider>().reset();
                    },
                    child: const Text('Log out'),
                  ),
                ]),
              ],
            ),
          ),

          _card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Academic standing', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15.5)),
                const Text('From the GPA Converter.', style: TextStyle(fontSize: 12.5, color: AppColors.inkSoft)),
                const SizedBox(height: 14),
                if (profile.gpaProfile != null) ...[
                  Row(children: [
                    Text(profile.gpaProfile!.gpa.toStringAsFixed(2), style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: AppColors.blue)),
                    const SizedBox(width: 12),
                    Expanded(child: Text('Unified GPA · ${profile.gpaProfile!.percent.toStringAsFixed(0)}% US-equivalent · ECTS ${profile.gpaProfile!.ects}',
                        style: const TextStyle(fontSize: 12.5, color: AppColors.inkSoft))),
                  ]),
                  const SizedBox(height: 12),
                  OutlinedButton(
                    onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const GpaConverterScreen())).then((_) => profile.loadAll()),
                    child: const Text('Update my grade'),
                  ),
                ] else ...[
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(10)),
                    child: const Text("You haven't converted a grade yet.", style: TextStyle(fontSize: 13, color: AppColors.inkSoft)),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const GpaConverterScreen())).then((_) => profile.loadAll()),
                      child: const Text('Open GPA Converter'),
                    ),
                  ),
                ],
              ],
            ),
          ),

          _card(
            child: Form(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Your details', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15.5)),
                  const Text('Used to score how well each scholarship fits you.', style: TextStyle(fontSize: 12.5, color: AppColors.inkSoft)),
                  const SizedBox(height: 14),
                  DropdownButtonFormField<String>(
                    value: _level,
                    decoration: const InputDecoration(labelText: 'Degree level seeking'),
                    items: ["Undergraduate", "Master's", "PhD", "Postdoc"].map((l) => DropdownMenuItem(value: l, child: Text(l))).toList(),
                    onChanged: (v) => setState(() => _level = v ?? _level),
                  ),
                  const SizedBox(height: 12),
                  TextField(controller: _fieldController, decoration: const InputDecoration(labelText: 'Field of study', hintText: 'e.g. Public health')),
                  const SizedBox(height: 12),
                  TextField(controller: _nationalityController, decoration: const InputDecoration(labelText: 'Nationality', hintText: 'e.g. Kenya')),
                  const SizedBox(height: 12),
                  Row(children: [
                    Expanded(child: TextField(controller: _ieltsController, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'IELTS score'))),
                    const SizedBox(width: 10),
                    Expanded(child: TextField(controller: _workYearsController, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Work years'))),
                  ]),
                  const SizedBox(height: 12),
                  TextField(controller: _publicationsController, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Publications')),
                  const SizedBox(height: 12),
                  Row(children: [
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: _leadership,
                        decoration: const InputDecoration(labelText: 'Leadership'),
                        items: ['None', 'Some', 'Extensive'].map((l) => DropdownMenuItem(value: l, child: Text(l))).toList(),
                        onChanged: (v) => setState(() => _leadership = v ?? _leadership),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: _volunteering,
                        decoration: const InputDecoration(labelText: 'Volunteering'),
                        items: ['None', 'Occasional', 'Regular'].map((l) => DropdownMenuItem(value: l, child: Text(l))).toList(),
                        onChanged: (v) => setState(() => _volunteering = v ?? _volunteering),
                      ),
                    ),
                  ]),
                  CheckboxListTile(
                    value: _hasCv, onChanged: (v) => setState(() => _hasCv = v ?? false),
                    title: const Text('I have a CV/resume ready', style: TextStyle(fontSize: 13.5)),
                    controlAffinity: ListTileControlAffinity.leading, contentPadding: EdgeInsets.zero, dense: true,
                  ),
                  CheckboxListTile(
                    value: _hasSop, onChanged: (v) => setState(() => _hasSop = v ?? false),
                    title: const Text('I have a Statement of Purpose ready', style: TextStyle(fontSize: 13.5)),
                    controlAffinity: ListTileControlAffinity.leading, contentPadding: EdgeInsets.zero, dense: true,
                  ),
                  CheckboxListTile(
                    value: _hasRecs, onChanged: (v) => setState(() => _hasRecs = v ?? false),
                    title: const Text('I have reference/recommendation letters ready', style: TextStyle(fontSize: 13.5)),
                    controlAffinity: ListTileControlAffinity.leading, contentPadding: EdgeInsets.zero, dense: true,
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: (!_initialized || _saving) ? null : _saveProfile,
                      child: const Text('Save profile'),
                    ),
                  ),
                ],
              ),
            ),
          ),

          _card(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Scholarship Readiness Score', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15.5)),
                const Text('Like a credit score for your scholarship applications.', style: TextStyle(fontSize: 12.5, color: AppColors.inkSoft)),
                const SizedBox(height: 14),
                if (profile.readiness == null)
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(10)),
                    child: const Text('Save your GPA and details above to see your readiness score.', style: TextStyle(fontSize: 13, color: AppColors.inkSoft)),
                  )
                else ...[
                  Row(crossAxisAlignment: CrossAxisAlignment.baseline, textBaseline: TextBaseline.alphabetic, children: [
                    Text('${profile.readiness!.overall}', style: const TextStyle(fontSize: 34, fontWeight: FontWeight.w800, color: AppColors.blue)),
                    const SizedBox(width: 8),
                    const Text('/ 100', style: TextStyle(fontSize: 12.5, color: AppColors.inkSoft)),
                  ]),
                  const SizedBox(height: 8),
                  ...profile.readiness!.categories.map((c) => Padding(
                        padding: const EdgeInsets.symmetric(vertical: 7),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(c.label, style: const TextStyle(fontSize: 13)),
                            Text('★' * c.stars + '☆' * (5 - c.stars), style: const TextStyle(color: AppColors.blue, letterSpacing: 1)),
                          ],
                        ),
                      )),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _card({required Widget child}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(16), border: Border.all(color: AppColors.line)),
      child: child,
    );
  }
}

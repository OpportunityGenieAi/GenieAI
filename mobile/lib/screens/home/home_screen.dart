import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/app_providers.dart';
import '../../providers/auth_provider.dart';
import '../../theme/app_theme.dart';
import '../../widgets/scholarship_card.dart';
import '../auth/login_screen.dart';
import '../auth/signup_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  static const _regions = ['All', 'UK', 'USA', 'Europe', 'Africa', 'Asia', 'Other'];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final auth = context.read<AuthProvider>();
      context.read<ScholarshipProvider>().fetch(auth: auth.isLoggedIn);
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final scholarships = context.watch<ScholarshipProvider>();
    final tracker = context.watch<TrackerProvider>();

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: () => scholarships.fetch(auth: auth.isLoggedIn),
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 100),
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Explore Scholarships', style: Theme.of(context).textTheme.bodySmall),
                    Text('Find Your Scholarship', style: Theme.of(context).textTheme.headlineMedium),
                  ],
                ),
                if (auth.isLoggedIn)
                  CircleAvatar(
                    radius: 22,
                    backgroundColor: AppColors.blueTint,
                    child: Text(auth.user!.name.substring(0, 1).toUpperCase(),
                        style: const TextStyle(color: AppColors.blue, fontWeight: FontWeight.w800)),
                  )
                else
                  IconButton.filled(
                    style: IconButton.styleFrom(backgroundColor: AppColors.blue),
                    onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const LoginScreen())),
                    icon: const Icon(Icons.login, color: Colors.white),
                  ),
              ],
            ),
            const SizedBox(height: 18),
            if (!auth.isLoggedIn)
              InkWell(
                borderRadius: BorderRadius.circular(16),
                onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const SignupScreen())),
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: AppColors.blue, borderRadius: BorderRadius.circular(16)),
                  child: Row(
                    children: [
                      Container(
                        width: 38, height: 38,
                        decoration: BoxDecoration(color: Colors.white.withOpacity(0.18), borderRadius: BorderRadius.circular(10)),
                        child: const Icon(Icons.lock_open, color: Colors.white, size: 19),
                      ),
                      const SizedBox(width: 14),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Create a free account', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 15.5)),
                            SizedBox(height: 2),
                            Text('Unlock Match scores, Tracker, Advisor & more', style: TextStyle(color: Colors.white70, fontSize: 12.5)),
                          ],
                        ),
                      ),
                      const Icon(Icons.arrow_forward, color: Colors.white, size: 18),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 22),
            Text('Latest Scholarships', style: Theme.of(context).textTheme.titleLarge),
            Text('${scholarships.items.length} opportunities worldwide', style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 14),
            TextField(
              decoration: const InputDecoration(
                hintText: 'Search scholarships, countries…',
                prefixIcon: Icon(Icons.search, size: 19, color: AppColors.inkFaint),
              ),
              onChanged: (v) {
                scholarships.setQuery(v);
                scholarships.fetch(auth: auth.isLoggedIn);
              },
            ),
            const SizedBox(height: 12),
            SizedBox(
              height: 40,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: _regions.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (context, i) {
                  final r = _regions[i];
                  final active = scholarships.region == r;
                  return ChoiceChip(
                    label: Text(r),
                    selected: active,
                    onSelected: (_) {
                      scholarships.setRegion(r);
                      scholarships.fetch(auth: auth.isLoggedIn);
                    },
                    selectedColor: AppColors.blue,
                    backgroundColor: AppColors.pill,
                    labelStyle: TextStyle(color: active ? Colors.white : AppColors.blue, fontWeight: FontWeight.w700, fontSize: 13.5),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20), side: BorderSide.none),
                  );
                },
              ),
            ),
            const SizedBox(height: 16),
            if (scholarships.loading)
              const Padding(padding: EdgeInsets.symmetric(vertical: 40), child: Center(child: CircularProgressIndicator()))
            else if (scholarships.items.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 40),
                child: Center(child: Text('No scholarships match those filters yet.', style: TextStyle(color: AppColors.inkSoft))),
              )
            else
              ...scholarships.items.map((s) => ScholarshipCard(
                    scholarship: s,
                    showMatch: auth.isLoggedIn,
                    isBookmarked: tracker.isTracked(s.id),
                    onToggleBookmark: () {
                      if (!auth.isLoggedIn) {
                        Navigator.of(context).push(MaterialPageRoute(builder: (_) => const SignupScreen()));
                        return;
                      }
                      tracker.toggle(s.id);
                    },
                  )),
          ],
        ),
      ),
    );
  }
}

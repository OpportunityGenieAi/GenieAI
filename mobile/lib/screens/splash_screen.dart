import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/auth_provider.dart';
import '../theme/app_theme.dart';
import 'main_shell.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});
  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await context.read<AuthProvider>().tryRestoreSession();
      if (mounted) {
        Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const MainShell()));
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: AppColors.bg,
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('OpportunityGenie AI', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18, color: AppColors.ink)),
            SizedBox(height: 16),
            CircularProgressIndicator(color: AppColors.blue),
          ],
        ),
      ),
    );
  }
}

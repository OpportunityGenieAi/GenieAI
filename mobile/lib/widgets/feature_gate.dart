import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/signup_screen.dart';

class FeatureGate extends StatelessWidget {
  final String title;
  final String body;
  const FeatureGate({super.key, required this.title, required this.body});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(30),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 64, height: 64,
                decoration: const BoxDecoration(color: AppColors.blueTint, shape: BoxShape.circle),
                child: const Icon(Icons.lock_outline, color: AppColors.blue, size: 28),
              ),
              const SizedBox(height: 18),
              Text(title, style: Theme.of(context).textTheme.headlineSmall, textAlign: TextAlign.center),
              const SizedBox(height: 8),
              Text(body, style: Theme.of(context).textTheme.bodySmall, textAlign: TextAlign.center),
              const SizedBox(height: 22),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const SignupScreen())),
                  child: const Text('Create a free account'),
                ),
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const LoginScreen())),
                child: const Text('I already have an account'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

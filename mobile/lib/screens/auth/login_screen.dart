import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/auth_provider.dart';
import '../../theme/app_theme.dart';
import 'forgot_password_screen.dart';
import 'signup_screen.dart';
import 'verify_email_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _submitting = false;

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _submitting = true);
    final auth = context.read<AuthProvider>();
    final result = await auth.login(_email.text.trim(), _password.text);
    setState(() => _submitting = false);
    if (!mounted) return;
    if (result == LoginResult.ok) {
      Navigator.of(context).popUntil((r) => r.isFirst);
    } else if (result == LoginResult.unverified) {
      // Password was right but the email isn't confirmed yet: send a fresh code.
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => VerifyEmailScreen(email: _email.text.trim(), autoResend: true)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final error = context.watch<AuthProvider>().error;
    return Scaffold(
      appBar: AppBar(leading: const BackButton()),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Welcome back', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 4),
              Text('Log in to see your scholarship matches.', style: Theme.of(context).textTheme.bodySmall),
              const SizedBox(height: 20),
              if (error != null)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 14),
                  decoration: BoxDecoration(color: AppColors.redTint, borderRadius: BorderRadius.circular(10)),
                  child: Text(error, style: const TextStyle(color: AppColors.red, fontSize: 12.5)),
                ),
              TextFormField(
                controller: _email,
                decoration: const InputDecoration(labelText: 'Email'),
                keyboardType: TextInputType.emailAddress,
                validator: (v) => (v == null || !v.contains('@')) ? 'Enter a valid email' : null,
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _password,
                decoration: const InputDecoration(labelText: 'Password'),
                obscureText: true,
                validator: (v) => (v == null || v.isEmpty) ? 'Enter your password' : null,
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _submitting ? null : _submit,
                  child: _submitting
                      ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Text('Log in'),
                ),
              ),
              const SizedBox(height: 16),
              Center(
                child: TextButton(
                  onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const ForgotPasswordScreen())),
                  child: const Text('Forgot your password?'),
                ),
              ),
              Center(
                child: TextButton(
                  onPressed: () => Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const SignupScreen())),
                  child: const Text("New here? Create an account"),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

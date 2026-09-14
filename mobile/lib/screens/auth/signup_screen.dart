import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../providers/auth_provider.dart';
import '../../theme/app_theme.dart';
import 'login_screen.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});
  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();
  final _securityAnswer = TextEditingController();
  String _securityQuestion = "What city were you born in?";
  bool _submitting = false;

  static const _questions = [
    "What city were you born in?",
    "What was your first school's name?",
    "What is your favourite subject?",
  ];

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_password.text != _confirm.text) {
      context.read<AuthProvider>();
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Passwords don't match.")));
      return;
    }
    setState(() => _submitting = true);
    final ok = await context.read<AuthProvider>().signup(
          name: _name.text.trim(),
          email: _email.text.trim(),
          password: _password.text,
          securityQuestion: _securityQuestion,
          securityAnswer: _securityAnswer.text,
        );
    setState(() => _submitting = false);
    if (ok && mounted) Navigator.of(context).popUntil((r) => r.isFirst);
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
              Text('Create your account', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 4),
              Text('Free — takes under a minute.', style: Theme.of(context).textTheme.bodySmall),
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
                controller: _name,
                decoration: const InputDecoration(labelText: 'Full name'),
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Enter your name' : null,
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _email,
                decoration: const InputDecoration(labelText: 'Email'),
                keyboardType: TextInputType.emailAddress,
                validator: (v) => (v == null || !v.contains('@')) ? 'Enter a valid email' : null,
              ),
              const SizedBox(height: 14),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _password,
                      decoration: const InputDecoration(labelText: 'Password'),
                      obscureText: true,
                      validator: (v) => (v == null || v.length < 6) ? 'Min 6 characters' : null,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: TextFormField(
                      controller: _confirm,
                      decoration: const InputDecoration(labelText: 'Confirm'),
                      obscureText: true,
                      validator: (v) => (v == null || v.length < 6) ? 'Min 6 characters' : null,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              DropdownButtonFormField<String>(
                value: _securityQuestion,
                decoration: const InputDecoration(labelText: 'Security question'),
                items: _questions.map((q) => DropdownMenuItem(value: q, child: Text(q, style: const TextStyle(fontSize: 13)))).toList(),
                onChanged: (v) => setState(() => _securityQuestion = v ?? _questions.first),
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _securityAnswer,
                decoration: const InputDecoration(labelText: 'Answer'),
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Enter an answer' : null,
              ),
              const SizedBox(height: 4),
              const Text("You'll need this to reset your password.", style: TextStyle(fontSize: 11.5, color: AppColors.inkSoft)),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _submitting ? null : _submit,
                  child: _submitting
                      ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Text('Create account'),
                ),
              ),
              const SizedBox(height: 16),
              Center(
                child: TextButton(
                  onPressed: () => Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const LoginScreen())),
                  child: const Text('Already registered? Log in'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

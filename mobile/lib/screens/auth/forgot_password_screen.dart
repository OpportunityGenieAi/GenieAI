import 'package:flutter/material.dart';

import '../../services/auth_service.dart';
import '../../theme/app_theme.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});
  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _authService = AuthService();
  final _emailController = TextEditingController();
  final _answerController = TextEditingController();
  final _newPasswordController = TextEditingController();

  int _step = 1;
  String? _question;
  String? _error;
  bool _busy = false;
  bool _done = false;

  Future<void> _startReset() async {
    setState(() { _busy = true; _error = null; });
    try {
      final q = await _authService.forgotPasswordStart(_emailController.text.trim());
      setState(() { _question = q; _step = 2; });
    } catch (e) {
      setState(() => _error = e.toString());
    }
    setState(() => _busy = false);
  }

  Future<void> _completeReset() async {
    setState(() { _busy = true; _error = null; });
    try {
      await _authService.forgotPasswordVerify(
        email: _emailController.text.trim(),
        securityAnswer: _answerController.text,
        newPassword: _newPasswordController.text,
      );
      setState(() => _done = true);
    } catch (e) {
      setState(() => _error = e.toString());
    }
    setState(() => _busy = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(leading: const BackButton()),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Reset your password', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 20),
            if (_error != null)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 14),
                decoration: BoxDecoration(color: AppColors.redTint, borderRadius: BorderRadius.circular(10)),
                child: Text(_error!, style: const TextStyle(color: AppColors.red, fontSize: 12.5)),
              ),
            if (_done)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: AppColors.greenTint, borderRadius: BorderRadius.circular(10)),
                child: const Text('Password updated — log in with your new password.', style: TextStyle(color: AppColors.green, fontSize: 12.5)),
              )
            else if (_step == 1) ...[
              TextField(controller: _emailController, decoration: const InputDecoration(labelText: 'Email'), keyboardType: TextInputType.emailAddress),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(onPressed: _busy ? null : _startReset, child: const Text('Continue')),
              ),
            ] else ...[
              Text(_question ?? '', style: Theme.of(context).textTheme.bodySmall),
              const SizedBox(height: 14),
              TextField(controller: _answerController, decoration: const InputDecoration(labelText: 'Answer')),
              const SizedBox(height: 14),
              TextField(controller: _newPasswordController, decoration: const InputDecoration(labelText: 'New password'), obscureText: true),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(onPressed: _busy ? null : _completeReset, child: const Text('Reset password')),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

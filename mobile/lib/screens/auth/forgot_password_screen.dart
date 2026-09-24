import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

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
  final _codeController = TextEditingController();
  final _newPasswordController = TextEditingController();

  int _step = 1;
  String? _error;
  String? _info;
  bool _busy = false;
  bool _done = false;

  Future<void> _sendCode() async {
    if (!_emailController.text.contains('@')) {
      setState(() => _error = 'Enter a valid email.');
      return;
    }
    setState(() { _busy = true; _error = null; _info = null; });
    try {
      await _authService.forgotPasswordStart(_emailController.text.trim());
      setState(() {
        _step = 2;
        _info = 'If an account exists for that email, a reset code is on its way.';
      });
    } catch (e) {
      setState(() => _error = e.toString());
    }
    setState(() => _busy = false);
  }

  Future<void> _completeReset() async {
    if (_codeController.text.trim().length < 6 || _newPasswordController.text.length < 6) {
      setState(() => _error = 'Enter the code from your email and a new password (6+ characters).');
      return;
    }
    setState(() { _busy = true; _error = null; });
    try {
      await _authService.forgotPasswordVerify(
        email: _emailController.text.trim(),
        code: _codeController.text.trim(),
        newPassword: _newPasswordController.text,
      );
      setState(() => _done = true);
    } catch (e) {
      setState(() => _error = e.toString());
    }
    setState(() => _busy = false);
  }

  Widget _box(String text, Color bg, Color fg) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(12),
        margin: const EdgeInsets.only(bottom: 14),
        decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(10)),
        child: Text(text, style: TextStyle(color: fg, fontSize: 12.5)),
      );

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
            if (_error != null) _box(_error!, AppColors.redTint, AppColors.red),
            if (_info != null && !_done) _box(_info!, AppColors.greenTint, AppColors.green),
            if (_done)
              _box('Password updated — log in with your new password.', AppColors.greenTint, AppColors.green)
            else if (_step == 1) ...[
              Text("Enter your account email and we'll send you a reset code.", style: Theme.of(context).textTheme.bodySmall),
              const SizedBox(height: 14),
              TextField(controller: _emailController, decoration: const InputDecoration(labelText: 'Email'), keyboardType: TextInputType.emailAddress),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(onPressed: _busy ? null : _sendCode, child: const Text('Send reset code')),
              ),
            ] else ...[
              TextField(
                controller: _codeController,
                keyboardType: TextInputType.number,
                maxLength: 10,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 22, letterSpacing: 6),
                decoration: const InputDecoration(labelText: 'Code from your email', counterText: ''),
              ),
              const SizedBox(height: 14),
              TextField(controller: _newPasswordController, decoration: const InputDecoration(labelText: 'New password'), obscureText: true),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(onPressed: _busy ? null : _completeReset, child: const Text('Reset password')),
              ),
              const SizedBox(height: 16),
              Center(child: TextButton(onPressed: _busy ? null : _sendCode, child: const Text("Didn't get it? Send a new code"))),
            ],
          ],
        ),
      ),
    );
  }
}

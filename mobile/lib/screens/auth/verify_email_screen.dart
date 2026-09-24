import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../../providers/auth_provider.dart';
import '../../services/auth_service.dart';
import '../../theme/app_theme.dart';

class VerifyEmailScreen extends StatefulWidget {
  final String email;
  final bool autoResend;
  const VerifyEmailScreen({super.key, required this.email, this.autoResend = false});
  @override
  State<VerifyEmailScreen> createState() => _VerifyEmailScreenState();
}

class _VerifyEmailScreenState extends State<VerifyEmailScreen> {
  final _authService = AuthService();
  final _code = TextEditingController();
  bool _busy = false;
  String? _info;
  String? _resendError;

  @override
  void initState() {
    super.initState();
    // Coming from a login attempt with an unconfirmed email: send a fresh code.
    if (widget.autoResend) _resend();
  }

  Future<void> _resend() async {
    setState(() { _info = null; _resendError = null; });
    try {
      await _authService.resendCode(widget.email);
      if (mounted) setState(() => _info = 'A new code is on its way. Check your inbox and spam folder.');
    } catch (e) {
      if (mounted) setState(() => _resendError = e.toString());
    }
  }

  Future<void> _submit() async {
    if (_code.text.trim().length < 6) return;
    setState(() => _busy = true);
    final ok = await context.read<AuthProvider>().verifyEmail(widget.email, _code.text.trim());
    if (!mounted) return;
    setState(() => _busy = false);
    if (ok) Navigator.of(context).popUntil((r) => r.isFirst);
  }

  @override
  Widget build(BuildContext context) {
    final error = _resendError ?? context.watch<AuthProvider>().error;
    return Scaffold(
      appBar: AppBar(leading: const BackButton()),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Check your email', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 4),
            Text(
              'We sent a confirmation code to ${widget.email}. Enter it below to activate your account.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 20),
            if (error != null)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 14),
                decoration: BoxDecoration(color: AppColors.redTint, borderRadius: BorderRadius.circular(10)),
                child: Text(error, style: const TextStyle(color: AppColors.red, fontSize: 12.5)),
              ),
            if (_info != null)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 14),
                decoration: BoxDecoration(color: AppColors.greenTint, borderRadius: BorderRadius.circular(10)),
                child: Text(_info!, style: const TextStyle(color: AppColors.green, fontSize: 12.5)),
              ),
            TextField(
              controller: _code,
              autofocus: true,
              keyboardType: TextInputType.number,
              maxLength: 10,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 22, letterSpacing: 6),
              decoration: const InputDecoration(labelText: 'Confirmation code', counterText: ''),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _busy ? null : _submit,
                child: _busy
                    ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Text('Confirm email'),
              ),
            ),
            const SizedBox(height: 16),
            Center(child: TextButton(onPressed: _resend, child: const Text("Didn't get it? Resend code"))),
          ],
        ),
      ),
    );
  }
}

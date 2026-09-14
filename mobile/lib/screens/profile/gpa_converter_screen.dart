import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/profile_models.dart';
import '../../providers/app_providers.dart';
import '../../theme/app_theme.dart';

class GpaConverterScreen extends StatefulWidget {
  const GpaConverterScreen({super.key});
  @override
  State<GpaConverterScreen> createState() => _GpaConverterScreenState();
}

class _GpaConverterScreenState extends State<GpaConverterScreen> {
  String? _systemId;
  final _valueController = TextEditingController();
  Map<String, dynamic>? _result;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final profile = context.read<ProfileProvider>();
      if (profile.systems.isEmpty) await profile.loadAll();
      setState(() => _systemId = profile.systems.isNotEmpty ? profile.systems.first.id : null);
    });
  }

  GradingSystem? _currentSystem(List<GradingSystem> systems) =>
      systems.where((s) => s.id == _systemId).cast<GradingSystem?>().firstOrNull;

  Future<void> _convert() async {
    if (_systemId == null || _valueController.text.trim().isEmpty) return;
    setState(() { _busy = true; _error = null; });
    try {
      final res = await context.read<ProfileProvider>().previewConversion(_systemId!, _valueController.text.trim());
      setState(() => _result = res);
    } catch (e) {
      setState(() => _error = 'Enter a valid value for this grading system.');
    }
    setState(() => _busy = false);
  }

  Future<void> _save() async {
    if (_systemId == null || _valueController.text.trim().isEmpty) return;
    setState(() => _busy = true);
    try {
      await context.read<ProfileProvider>().saveGpa(_systemId!, _valueController.text.trim());
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Saved to your profile.')));
      }
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Could not save — try again.')));
    }
    setState(() => _busy = false);
  }

  @override
  Widget build(BuildContext context) {
    final profile = context.watch<ProfileProvider>();
    final system = _currentSystem(profile.systems);

    return Scaffold(
      appBar: AppBar(leading: const BackButton(), title: const Text('GPA Converter')),
      body: profile.systems.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Text('Flagship feature', style: Theme.of(context).textTheme.bodySmall),
                const SizedBox(height: 2),
                Text('Turn your local grade into a unified 4.0 GPA, a US-equivalent percentage, and an ECTS grade.',
                    style: Theme.of(context).textTheme.bodySmall),
                const SizedBox(height: 20),
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(16), border: Border.all(color: AppColors.line)),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Enter your grade', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontSize: 15.5)),
                      const SizedBox(height: 14),
                      DropdownButtonFormField<String>(
                        value: _systemId,
                        isExpanded: true,
                        decoration: const InputDecoration(labelText: 'Your grading system'),
                        items: profile.systems
                            .map((s) => DropdownMenuItem(value: s.id, child: Text(s.label, style: const TextStyle(fontSize: 12.5), overflow: TextOverflow.ellipsis)))
                            .toList(),
                        onChanged: (v) => setState(() { _systemId = v; _result = null; _valueController.clear(); }),
                      ),
                      const SizedBox(height: 14),
                      if (system?.inputType == 'select')
                        DropdownButtonFormField<String>(
                          value: _valueController.text.isNotEmpty ? _valueController.text : null,
                          decoration: const InputDecoration(labelText: 'Your grade'),
                          items: (system?.options ?? []).map((o) => DropdownMenuItem(value: o, child: Text(o))).toList(),
                          onChanged: (v) => setState(() => _valueController.text = v ?? ''),
                        )
                      else
                        TextField(
                          controller: _valueController,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          decoration: InputDecoration(
                            labelText: 'Your grade',
                            helperText: system != null ? 'Scale: ${system.min}–${system.max}' : null,
                          ),
                        ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: _busy ? null : _convert,
                          child: const Text('Convert'),
                        ),
                      ),
                    ],
                  ),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 10),
                  Text(_error!, style: const TextStyle(color: AppColors.red, fontSize: 12.5)),
                ],
                if (_result != null) ...[
                  const SizedBox(height: 14),
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(16), border: Border.all(color: AppColors.line)),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Your unified profile', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontSize: 15.5)),
                        const SizedBox(height: 10),
                        Text('${(_result!['gpa'] as num).toStringAsFixed(2)}',
                            style: const TextStyle(fontSize: 36, fontWeight: FontWeight.w800, color: AppColors.blue)),
                        const Text('Unified GPA out of 4.0', style: TextStyle(fontSize: 12.5, color: AppColors.inkSoft)),
                        const SizedBox(height: 10),
                        _resultRow('US-equivalent percentage', '${_result!['percent']}%'),
                        _resultRow('ECTS grade', '${_result!['ects']}'),
                        const SizedBox(height: 10),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(10)),
                          child: Text('${_result!['percentile_note']}', style: const TextStyle(fontSize: 12.5, color: AppColors.inkSoft)),
                        ),
                        const SizedBox(height: 14),
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(onPressed: _busy ? null : _save, child: const Text('Save to my profile')),
                        ),
                        const SizedBox(height: 10),
                        const Text(
                          "These figures are estimates for planning purposes and don't replace an official credential evaluation.",
                          style: TextStyle(fontSize: 11, color: AppColors.inkFaint),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
    );
  }

  Widget _resultRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 13)),
          Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

extension _FirstOrNull<T> on Iterable<T> {
  T? get firstOrNull => isEmpty ? null : first;
}

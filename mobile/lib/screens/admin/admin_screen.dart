import 'package:flutter/material.dart';

import '../../models/scholarship.dart';
import '../../services/domain_services.dart';
import '../../theme/app_theme.dart';

class AdminScreen extends StatefulWidget {
  const AdminScreen({super.key});
  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> {
  final _service = ScholarshipService();
  List<Scholarship> _items = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    _items = await _service.list(auth: true);
    setState(() => _loading = false);
  }

  Future<void> _delete(Scholarship s) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Remove this listing?'),
        content: Text('This removes "${s.name}" for every visitor.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete')),
        ],
      ),
    );
    if (confirmed == true) {
      await _service.delete(s.id);
      _load();
    }
  }

  Future<void> _openForm({Scholarship? existing}) async {
    final saved = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => ScholarshipFormScreen(existing: existing)),
    );
    if (saved == true) _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(leading: const BackButton(), title: const Text('Admin')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                const Text('Changes appear for every visitor immediately.', style: TextStyle(fontSize: 13, color: AppColors.inkSoft)),
                const SizedBox(height: 14),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(onPressed: () => _openForm(), child: const Text('+ Add scholarship')),
                ),
                const SizedBox(height: 16),
                ..._items.map((s) => Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(color: AppColors.card, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(12)),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(s.name, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14)),
                                const SizedBox(height: 2),
                                Text('${s.country} · ${s.level} · ${s.funding}', style: const TextStyle(fontSize: 12, color: AppColors.inkSoft)),
                              ],
                            ),
                          ),
                          IconButton(onPressed: () => _openForm(existing: s), icon: const Icon(Icons.edit_outlined, size: 19)),
                          IconButton(onPressed: () => _delete(s), icon: const Icon(Icons.delete_outline, size: 19, color: AppColors.red)),
                        ],
                      ),
                    )),
                const SizedBox(height: 10),
                const Text(
                  'For production, keep this data on the real backend (already the case here) behind role-based admin accounts and audit logging.',
                  style: TextStyle(fontSize: 11.5, color: AppColors.inkFaint),
                ),
              ],
            ),
    );
  }
}

class ScholarshipFormScreen extends StatefulWidget {
  final Scholarship? existing;
  const ScholarshipFormScreen({super.key, this.existing});
  @override
  State<ScholarshipFormScreen> createState() => _ScholarshipFormScreenState();
}

class _ScholarshipFormScreenState extends State<ScholarshipFormScreen> {
  final _service = ScholarshipService();
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _name, _provider, _country, _level, _field, _deadline, _link, _tags, _blurb;
  String _funding = 'Fully-funded';
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    _name = TextEditingController(text: e?.name ?? '');
    _provider = TextEditingController(text: e?.provider ?? '');
    _country = TextEditingController(text: e?.country ?? '');
    _level = TextEditingController(text: e?.level ?? '');
    _field = TextEditingController(text: e?.field ?? 'All fields');
    _deadline = TextEditingController(text: e?.deadlineWindow ?? '');
    _link = TextEditingController(text: e?.officialLink ?? '');
    _tags = TextEditingController(text: e?.tags.join(', ') ?? '');
    _blurb = TextEditingController(text: e?.blurb ?? '');
    _funding = e?.funding ?? 'Fully-funded';
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    final scholarship = Scholarship(
      id: widget.existing?.id ?? '',
      name: _name.text.trim(),
      provider: _provider.text.trim(),
      country: _country.text.trim(),
      level: _level.text.trim(),
      field: _field.text.trim().isEmpty ? 'All fields' : _field.text.trim(),
      funding: _funding,
      deadlineWindow: _deadline.text.trim(),
      officialLink: _link.text.trim(),
      tags: _tags.text.split(',').map((t) => t.trim()).where((t) => t.isNotEmpty).toList(),
      blurb: _blurb.text.trim(),
    );
    try {
      if (widget.existing == null) {
        await _service.create(scholarship);
      } else {
        await _service.update(widget.existing!.id, scholarship);
      }
      if (mounted) Navigator.pop(context, true);
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Could not save — check the fields and try again.')));
    }
    setState(() => _saving = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(leading: const BackButton(), title: Text(widget.existing == null ? 'Add scholarship' : 'Edit scholarship')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextFormField(controller: _name, decoration: const InputDecoration(labelText: 'Scholarship name'), validator: _required),
              const SizedBox(height: 12),
              TextFormField(controller: _provider, decoration: const InputDecoration(labelText: 'Provider / organization'), validator: _required),
              const SizedBox(height: 12),
              TextFormField(controller: _country, decoration: const InputDecoration(labelText: 'Country / region'), validator: _required),
              const SizedBox(height: 12),
              TextFormField(controller: _level, decoration: const InputDecoration(labelText: 'Degree level'), validator: _required),
              const SizedBox(height: 12),
              TextFormField(controller: _field, decoration: const InputDecoration(labelText: 'Field of study')),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: _funding,
                decoration: const InputDecoration(labelText: 'Funding type'),
                items: ['Fully-funded', 'Partial', 'Partial grant'].map((f) => DropdownMenuItem(value: f, child: Text(f))).toList(),
                onChanged: (v) => setState(() => _funding = v ?? _funding),
              ),
              const SizedBox(height: 12),
              TextFormField(controller: _deadline, decoration: const InputDecoration(labelText: 'Deadline window'), validator: _required),
              const SizedBox(height: 12),
              TextFormField(controller: _link, decoration: const InputDecoration(labelText: 'Official application link'), validator: _required, keyboardType: TextInputType.url),
              const SizedBox(height: 12),
              TextFormField(controller: _tags, decoration: const InputDecoration(labelText: 'Tags (comma separated)')),
              const SizedBox(height: 12),
              TextFormField(controller: _blurb, decoration: const InputDecoration(labelText: 'Short description'), maxLines: 3, validator: _required),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _saving ? null : _save,
                  child: Text(widget.existing == null ? 'Add scholarship' : 'Save changes'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String? _required(String? v) => (v == null || v.trim().isEmpty) ? 'Required' : null;
}

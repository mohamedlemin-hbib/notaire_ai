import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/language_provider.dart';

class AddUserScreen extends StatefulWidget {
  final Map<String, dynamic>? user;
  const AddUserScreen({super.key, this.user});

  @override
  State<AddUserScreen> createState() => _AddUserScreenState();
}

class _AddUserScreenState extends State<AddUserScreen> {
  final _emailController = TextEditingController();
  final _passController = TextEditingController();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _bureauController = TextEditingController();
  final _birthDateController = TextEditingController();
  final _nniController = TextEditingController();
  final _phoneController = TextEditingController();
  String _selectedRole = 'NOTAIRE';
  bool _isLoading = false;

  bool get _isEditing => widget.user != null;

  @override
  void initState() {
    super.initState();
    if (_isEditing) {
      final u = widget.user!;
      _emailController.text = u['email'] ?? '';
      _firstNameController.text = u['first_name'] ?? '';
      _lastNameController.text = u['last_name'] ?? '';
      _birthDateController.text = u['birth_date'] ?? '';
      _bureauController.text = u['bureau'] ?? '';
      _nniController.text = u['nni'] ?? '';
      _phoneController.text = u['phone_number'] ?? '';
      _selectedRole = u['role']?.toString().toUpperCase() ?? 'NOTAIRE';
    }
  }

  Future<void> _handleSaveUser() async {
    final lp = Provider.of<LanguageProvider>(context, listen: false);
    if (_lastNameController.text.isEmpty || (!_isEditing && _passController.text.isEmpty)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(lp.isArabic ? "الاسم وكلمة المرور مطلوبان" : "Le nom et le mot de passe sont requis")),
      );
      return;
    }

    // Nouvelle règle de sécurité : Mot de passe != Nom ou Téléphone
    if (!_isEditing && (_passController.text == _lastNameController.text || _passController.text == _phoneController.text)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(lp.isArabic 
          ? "كلمة المرور لا peut pas être identique à votre nom ou téléphone" 
          : "Le mot de passe ne peut pas être identique à votre nom ou téléphone")),
      );
      return;
    }

    // Validation du NNI (doit avoir exactement 10 chiffres s'il est fourni)
    if (_nniController.text.isNotEmpty && _nniController.text.length != 10) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(lp.translate('nni_10_digits'))),
      );
      return;
    }

    setState(() => _isLoading = true);
    try {
      final userData = {
        'email': _emailController.text.isEmpty ? null : _emailController.text,
        'first_name': _firstNameController.text.isEmpty ? null : _firstNameController.text,
        'last_name': _lastNameController.text.isEmpty ? null : _lastNameController.text,
        'birth_date': _birthDateController.text.isEmpty ? null : _birthDateController.text,
        'role': _selectedRole,
        'bureau': _bureauController.text.isEmpty ? null : _bureauController.text,
        'nni': _nniController.text.isEmpty ? null : _nniController.text,
        'phone_number': _phoneController.text.isEmpty ? null : _phoneController.text,
      };

      if (_passController.text.isNotEmpty) {
        userData['password'] = _passController.text;
      }

      final dynamic result;
      if (_isEditing) {
        result = await ApiService.updateUser(widget.user!['id'], userData);
      } else {
        result = await ApiService.createUser(userData);
      }

      if (result['success'] == true) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(_isEditing ? lp.translate('notary_updated') : lp.translate('notary_created'))),
          );
          Navigator.pop(context);
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("${lp.translate('fail')} : ${result['error'] ?? '...'}")),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Erreur: $e")),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final lp = Provider.of<LanguageProvider>(context);

    return Scaffold(
      appBar: AppBar(title: Text(_isEditing ? lp.translate('edit_notary') : lp.translate('add_notary'))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            TextField(
              controller: _firstNameController,
              decoration: InputDecoration(labelText: lp.translate('first_name')),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _lastNameController,
              decoration: InputDecoration(labelText: lp.translate('last_name')),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _passController,
              decoration: InputDecoration(
                labelText: _isEditing 
                  ? "${lp.translate('password_label')} (${lp.translate('pass_edit_hint')})" 
                  : "${lp.translate('password_label')} *",
              ),
              obscureText: true,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _nniController,
              decoration: InputDecoration(
                labelText: lp.translate('nni_label'),
                hintText: lp.translate('nni_hint'),
              ),
              keyboardType: TextInputType.number,
              inputFormatters: [
                FilteringTextInputFormatter.digitsOnly,
                LengthLimitingTextInputFormatter(10),
              ],
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _birthDateController,
              decoration: InputDecoration(
                labelText: "${lp.translate('birth_date')} (${lp.translate('birth_date_hint')})"
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _phoneController,
              decoration: InputDecoration(
                labelText: lp.translate('phone_label'),
                hintText: lp.translate('phone_hint'),
              ),
              keyboardType: TextInputType.phone,
              inputFormatters: [
                FilteringTextInputFormatter.digitsOnly,
                LengthLimitingTextInputFormatter(8),
              ],
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _bureauController,
              decoration: InputDecoration(labelText: lp.translate('bureau_label')),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: ['ADMIN', 'NOTAIRE'].contains(_selectedRole) ? _selectedRole : 'NOTAIRE',
              decoration: InputDecoration(labelText: lp.translate('role_label')),
              items: [
                DropdownMenuItem(value: 'ADMIN', child: Text(lp.translate('admin'))),
                DropdownMenuItem(value: 'NOTAIRE', child: Text(lp.translate('clerk'))),
              ],
              onChanged: (val) {
                if (val != null) setState(() => _selectedRole = val);
              },
            ),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _handleSaveUser,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1A237E),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: _isLoading 
                  ? const CircularProgressIndicator(color: Colors.white) 
                  : Text(lp.translate('save'), style: const TextStyle(fontSize: 18)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

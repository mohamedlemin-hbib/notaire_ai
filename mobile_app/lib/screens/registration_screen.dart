import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/language_provider.dart';

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({super.key});

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen> {
  final _emailController = TextEditingController();
  final _passController = TextEditingController();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  bool _isLoading = false;

  Future<void> _handleRegister() async {
    final lp = Provider.of<LanguageProvider>(context, listen: false);
    if (_firstNameController.text.isEmpty || _passController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(lp.isArabic ? "الاسم وكلمة المرور مطلوبان" : "Le nom et le mot de passe sont requis")),
      );
      return;
    }

    // Sécurité : Mot de passe != Nom
    if (_passController.text == _firstNameController.text || _passController.text == _lastNameController.text) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(lp.isArabic 
          ? "كلمة المرور لا peut pas être identique à votre nom" 
          : "Le mot de passe ne peut pas être identique à votre nom")),
      );
      return;
    }

    setState(() => _isLoading = true);
    try {
      final success = await ApiService.register({
        'first_name': _firstNameController.text,
        'last_name': _lastNameController.text,
        'email': null,
        'role': 'NOTAIRE',
        'password': _passController.text,
      });

      if (success) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(lp.translate('register_success'))),
          );
          Navigator.pushReplacementNamed(context, '/');
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(lp.translate('register_fail'))),
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
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(title: Text(lp.translate('register_title'))),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.person_add_rounded, size: 80, color: Color(0xFF1A237E)),
              const SizedBox(height: 16),
              Text(
                lp.translate('new_account'),
                style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Color(0xFF1A237E)),
              ),
              const SizedBox(height: 32),
              TextField(
                controller: _firstNameController,
                decoration: InputDecoration(
                  labelText: lp.translate('first_name'),
                  prefixIcon: const Icon(Icons.person_outline, color: Color(0xFF1A237E)),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                style: const TextStyle(color: Colors.black),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _lastNameController,
                decoration: InputDecoration(
                  labelText: lp.translate('last_name'),
                  prefixIcon: const Icon(Icons.person_outline, color: Color(0xFF1A237E)),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                style: const TextStyle(color: Colors.black),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _passController,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: "${lp.translate('password_label')} *",
                  prefixIcon: const Icon(Icons.lock_outline, color: Color(0xFF1A237E)),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                style: const TextStyle(color: Colors.black),
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _handleRegister,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1A237E),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: _isLoading 
                    ? const CircularProgressIndicator(color: Colors.white) 
                    : Text(lp.translate('register_button'), style: const TextStyle(fontSize: 18)),
                ),
              ),
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text(lp.translate('already_account'), style: const TextStyle(color: Color(0xFF1A237E))),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';

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
    }
  }

  Future<void> _handleSaveUser() async {
    if (_emailController.text.isEmpty || (!_isEditing && _passController.text.isEmpty)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Email et mot de passe sont obligatoires.")),
      );
      return;
    }

    // Validation du NNI (doit avoir exactement 10 chiffres s'il est fourni)
    if (_nniController.text.isNotEmpty && _nniController.text.length != 10) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Le NNI doit comporter exactement 10 chiffres.")),
      );
      return;
    }

    setState(() => _isLoading = true);
    try {
      final userData = {
        'email': _emailController.text,
        'first_name': _firstNameController.text,
        'last_name': _lastNameController.text,
        'birth_date': _birthDateController.text,
        'bureau': _bureauController.text,
        'nni': _nniController.text,
        'role': 'notaire',
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
            SnackBar(content: Text(_isEditing ? "Notaire mis à jour." : "Notaire créé avec succès.")),
          );
          Navigator.pop(context);
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("Échec : ${result['error'] ?? 'Erreur inconnue'}")),
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
    return Scaffold(
      appBar: AppBar(title: Text(_isEditing ? "Modifier le Notaire" : "Ajouter un Notaire")),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            TextField(
              controller: _firstNameController,
              decoration: const InputDecoration(labelText: "Prénom"),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _lastNameController,
              decoration: const InputDecoration(labelText: "Nom"),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _emailController,
              decoration: const InputDecoration(labelText: "Email *"),
              keyboardType: TextInputType.emailAddress,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _passController,
              decoration: InputDecoration(
                labelText: _isEditing ? "Mot de passe (laisser vide pour ne pas changer)" : "Mot de passe *",
              ),
              obscureText: true,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _nniController,
              decoration: const InputDecoration(
                labelText: "NNI (Numéro National d'Identité)",
                hintText: "10 chiffres requis",
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
              decoration: const InputDecoration(labelText: "Date de Naissance (ex: 01/01/1980)"),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _bureauController,
              decoration: const InputDecoration(labelText: "Numéro du Bureau"),
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
                  : const Text("Enregistrer", style: TextStyle(fontSize: 18)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

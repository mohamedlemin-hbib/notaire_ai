import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/language_provider.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  Map<String, dynamic>? _userProfile;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchProfile();
  }

  Future<void> _fetchProfile() async {
    setState(() => _isLoading = true);
    try {
      final profile = await ApiService.getMe();
      setState(() => _userProfile = profile);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Erreur lors de la récupération du profil: $e")),
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
      backgroundColor: const Color(0xFFF1F4F9),
      appBar: AppBar(
        title: Text(lp.translate('my_profile')),
        centerTitle: true,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _userProfile == null
              ? Center(child: Text(lp.translate('unable_load_profile')))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      const CircleAvatar(
                        radius: 50,
                        backgroundColor: Color(0xFF1A237E),
                        child: Icon(Icons.person, size: 60, color: Colors.white),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        _userProfile!['full_name'] ?? lp.translate('welcome_back'),
                        style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                      ),
                      Text(
                        _userProfile!['role'].toString().toUpperCase(),
                        style: const TextStyle(color: Colors.grey, fontWeight: FontWeight.w500),
                      ),
                      const SizedBox(height: 32),
                      _buildInfoCard(lp),
                      const SizedBox(height: 32),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: () => _handleLogout(lp),
                          icon: const Icon(Icons.logout),
                          label: Text(lp.translate('logout')),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.red[50],
                            foregroundColor: Colors.red,
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            elevation: 0,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }

  void _handleLogout(LanguageProvider lp) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text(lp.translate('logout')),
        content: Text(lp.translate('logout_confirm')),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(lp.translate('cancel'))),
          ElevatedButton(
            onPressed: () async {
              await ApiService.logout();
              if (mounted) {
                Navigator.pop(context);
                Navigator.pushReplacementNamed(context, '/');
              }
            },
            style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red, foregroundColor: Colors.white),
            child: Text(lp.translate('logout')),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoCard(LanguageProvider lp) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 5)),
        ],
      ),
      child: Column(
        children: [
          _buildInfoRow(Icons.phone_android_outlined, lp.translate('phone_label'), _userProfile!['phone_number'] ?? "—"),
          const Divider(height: 32),
          _buildInfoRow(Icons.business_outlined, lp.translate('bureau'), _userProfile!['bureau'] ?? lp.translate('not_specified')),
          const Divider(height: 32),
          _buildInfoRow(Icons.cake_outlined, lp.translate('birth_date'), _userProfile!['birth_date'] ?? lp.translate('not_specified')),
          const Divider(height: 32),
          _buildInfoRow(Icons.person_outline, lp.translate('first_name'), _userProfile!['first_name'] ?? "—"),
          const Divider(height: 32),
          _buildInfoRow(Icons.person_outline, lp.translate('last_name'), _userProfile!['last_name'] ?? "—"),
        ],
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Row(
      children: [
        Icon(icon, color: const Color(0xFF1A237E)),
        const SizedBox(width: 16),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
            Text(value, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
          ],
        ),
      ],
    );
  }
}

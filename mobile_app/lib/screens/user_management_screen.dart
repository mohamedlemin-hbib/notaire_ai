import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/language_provider.dart';
import 'add_user_screen.dart';

class UserManagementScreen extends StatefulWidget {
  const UserManagementScreen({super.key});

  @override
  State<UserManagementScreen> createState() => _UserManagementScreenState();
}

class _UserManagementScreenState extends State<UserManagementScreen> {
  List<dynamic> _users = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchUsers();
  }

  Future<void> _fetchUsers() async {
    final lp = Provider.of<LanguageProvider>(context, listen: false);
    setState(() => _isLoading = true);
    try {
      final users = await ApiService.getUsers();
      setState(() => _users = users);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("${lp.translate('error_fetching_users')}: $e")),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _deleteUser(int userId) async {
    final lp = Provider.of<LanguageProvider>(context, listen: false);
    try {
      final success = await ApiService.deleteUser(userId);
      if (success) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(lp.translate('user_deactivated'))),
          );
          _fetchUsers();
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Erreur: $e")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final lp = Provider.of<LanguageProvider>(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(lp.translate('manage_users')),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchUsers,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _users.isEmpty
              ? Center(child: Text(lp.translate('no_notary_found')))
              : ListView.builder(
                  itemCount: _users.length,
                  itemBuilder: (context, index) {
                    final user = _users[index];
                    final isActive = user['is_active'] == 1;
                    return Card(
                      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: isActive ? Colors.green : Colors.grey,
                          child: const Icon(Icons.person, color: Colors.white),
                        ),
                        title: Text(user['full_name'] ?? user['email']),
                        subtitle: Text("${user['email']} - ${user['role']}"),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            IconButton(
                              icon: const Icon(Icons.edit, color: Colors.blue),
                              onPressed: () => Navigator.push(
                                context,
                                MaterialPageRoute(builder: (context) => AddUserScreen(user: user)),
                              ).then((_) => _fetchUsers()),
                            ),
                            IconButton(
                              icon: const Icon(Icons.delete, color: Colors.red),
                              onPressed: () => _confirmDelete(user['id'], lp),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.pushNamed(context, '/admin/users/add').then((_) => _fetchUsers()),
        child: const Icon(Icons.add),
      ),
    );
  }

  void _confirmDelete(int userId, LanguageProvider lp) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text(lp.translate('confirm_deactivation')),
        content: Text(lp.translate('confirm_deactivation_desc')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text(lp.translate('cancel'))),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _deleteUser(userId);
            },
            child: Text(lp.translate('deactivate'), style: const TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }
}

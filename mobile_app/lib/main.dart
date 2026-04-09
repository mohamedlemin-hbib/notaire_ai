import 'package:flutter/material.dart';
import 'package:mobile_app/screens/chat_screen.dart';
import 'package:mobile_app/screens/login_screen.dart';
import 'package:mobile_app/screens/document_list_screen.dart';
import 'package:mobile_app/screens/profile_screen.dart';
import 'package:mobile_app/screens/user_management_screen.dart';
import 'package:mobile_app/screens/add_user_screen.dart';
import 'package:mobile_app/services/api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiService.init();
  runApp(const NotaireAIApp());
}

class NotaireAIApp extends StatelessWidget {
  const NotaireAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Notaire IA',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1A237E),
          surface: const Color(0xFFF6F8FC),
          brightness: Brightness.light,
        ),
        scaffoldBackgroundColor: const Color(0xFFF6F8FC),
        useMaterial3: true,
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.transparent,
          elevation: 0,
          centerTitle: false,
        ),
      ),
      initialRoute: ApiService.isAuthenticated ? '/chat' : '/',
      routes: {
        '/': (context) => const LoginScreen(),
        '/chat': (context) => const ChatScreen(),
        '/documents': (context) => const DocumentListScreen(),
        '/profile': (context) => const ProfileScreen(),
        '/admin/users': (context) => const UserManagementScreen(),
        '/admin/users/add': (context) => const AddUserScreen(),
      },
    );
  }
}

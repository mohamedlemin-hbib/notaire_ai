import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:mobile_app/providers/language_provider.dart';
import 'package:mobile_app/services/api_service.dart';
import 'package:mobile_app/screens/login_screen.dart';
import 'package:mobile_app/screens/chat_screen.dart';
import 'package:mobile_app/screens/document_list_screen.dart';
import 'package:mobile_app/screens/profile_screen.dart';
import 'package:mobile_app/screens/user_management_screen.dart';
import 'package:mobile_app/screens/add_user_screen.dart';
import 'package:mobile_app/screens/search_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiService.init();
  await initializeDateFormatting('fr_FR', null);
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => LanguageProvider()),
      ],
      child: const NotaireAIApp(),
    ),
  );
}

class NotaireAIApp extends StatelessWidget {
  const NotaireAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    final lp = Provider.of<LanguageProvider>(context);

    return MaterialApp(
      title: lp.translate('app_title'),
      debugShowCheckedModeBanner: false,
      locale: lp.currentLocale,
      supportedLocales: const [
        Locale('fr', 'FR'),
        Locale('ar', 'MA'),
      ],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
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
        '/search': (context) => const SearchScreen(),
      },
    );
  }
}

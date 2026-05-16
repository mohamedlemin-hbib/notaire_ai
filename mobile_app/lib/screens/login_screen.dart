import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/language_provider.dart';
import 'otp_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passController = TextEditingController();
  bool _isLoading = false;
  bool _obscurePassword = true;

  Future<void> _handleLogin() async {
    final lp = Provider.of<LanguageProvider>(context, listen: false);
    setState(() => _isLoading = true);
    try {
      final result = await ApiService.login(_emailController.text, _passController.text);
      if (result['requires_otp'] == true) {
        if (mounted) {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => OtpScreen(
                email: result['email'],
                phoneNumber: result['phone_number'],
              ),
            ),
          );
        }
      } else if (result['success'] == true) {
        if (mounted) Navigator.pushReplacementNamed(context, '/chat');
      } else {
        if (mounted) {
           ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(result['error'] ?? (lp.isArabic ? "فشل تسجيل الدخول. تحقق من بياناتك." : "Échec de connexion. Vérifiez vos identifiants."))),
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
    final primaryColor = const Color(0xFF1A237E);

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        automaticallyImplyLeading: false,
        actions: [
          TextButton.icon(
            onPressed: () => lp.toggleLanguage(),
            icon: const Icon(Icons.language, color: Color(0xFF1A237E)),
            label: Text(
              lp.isArabic ? "Français" : "العربية",
              style: const TextStyle(color: Color(0xFF1A237E), fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              ColorFiltered(
                colorFilter: const ColorFilter.mode(
                  Colors.white,
                  BlendMode.multiply,
                ),
                child: Image.asset('assets/images/logo.png', height: 120),
              ),
              const SizedBox(height: 48),
              Align(
                alignment: lp.isArabic ? Alignment.centerRight : Alignment.centerLeft,
                child: Text(
                  lp.isArabic ? "الاسم أو رقم الهاتف" : "Nom ou Numéro de téléphone",
                  style: TextStyle(color: primaryColor, fontWeight: FontWeight.bold),
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _emailController,
                maxLength: 8,
                decoration: InputDecoration(
                  prefixIcon: const Icon(Icons.person_outline, color: Color(0xFF1A237E)),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  counterText: "",
                ),
                style: const TextStyle(color: Colors.black),
              ),
              const SizedBox(height: 20),
              Align(
                alignment: lp.isArabic ? Alignment.centerRight : Alignment.centerLeft,
                child: Text(
                  lp.isArabic ? "كلمة المرور" : "Mot de passe",
                  style: TextStyle(color: primaryColor, fontWeight: FontWeight.bold),
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _passController,
                obscureText: _obscurePassword,
                decoration: InputDecoration(
                  prefixIcon: const Icon(Icons.lock_outline, color: Color(0xFF1A237E)),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                      color: const Color(0xFF1A237E),
                    ),
                    onPressed: () {
                      setState(() => _obscurePassword = !_obscurePassword);
                    },
                  ),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                style: const TextStyle(color: Colors.black),
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _handleLogin,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1A237E),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: _isLoading 
                    ? const CircularProgressIndicator(color: Colors.white) 
                    : Text(lp.translate('login_button'), style: const TextStyle(fontSize: 18)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// Fixed a typo in the class name for the rounded border
class RoundedRectangleRectangle extends RoundedRectangleBorder {
  const RoundedRectangleRectangle({super.borderRadius});
}

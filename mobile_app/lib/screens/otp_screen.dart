import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/language_provider.dart';

class OtpScreen extends StatefulWidget {
  final String email;
  final String? phoneNumber;
  const OtpScreen({super.key, required this.email, this.phoneNumber});

  @override
  State<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends State<OtpScreen> {
  final List<TextEditingController> _controllers = List.generate(6, (_) => TextEditingController());
  final List<FocusNode> _focusNodes = List.generate(6, (_) => FocusNode());
  bool _isLoading = false;
  int _secondsRemaining = 120; // 2 minutes
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  void _startTimer() {
    _timer?.cancel();
    _secondsRemaining = 120;
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_secondsRemaining > 0) {
        setState(() => _secondsRemaining--);
      } else {
        _timer?.cancel();
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    for (var controller in _controllers) {
      controller.dispose();
    }
    for (var node in _focusNodes) {
      node.dispose();
    }
    super.dispose();
  }

  Future<void> _verifyOtp() async {
    String code = _controllers.map((c) => c.text).join();
    if (code.length < 6) return;

    setState(() => _isLoading = true);
    try {
      final success = await ApiService.verifyOtp(widget.email, code);
      if (success) {
        if (mounted) Navigator.pushReplacementNamed(context, '/chat');
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Code invalide ou expiré.")),
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

  Future<void> _resendOtp() async {
    if (_secondsRemaining > 0) return;
    
    setState(() => _isLoading = true);
    try {
      final success = await ApiService.resendOtp(widget.email);
      if (success) {
        _startTimer();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Nouveau code envoyé.")),
          );
        }
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  String _formatTime(int seconds) {
    int mins = seconds ~/ 60;
    int secs = seconds % 60;
    return "$mins:${secs.toString().padLeft(2, '0')}";
  }

  @override
  Widget build(BuildContext context) {
    final lp = Provider.of<LanguageProvider>(context);
    final primaryColor = const Color(0xFF1A237E);
    final displayContact = widget.phoneNumber ?? widget.email;

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: primaryColor),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 20),
              ColorFiltered(
                colorFilter: const ColorFilter.mode(
                  Colors.white,
                  BlendMode.multiply,
                ),
                child: Image.asset('assets/images/logo.png', height: 80),
              ),
              const SizedBox(height: 32),
              Text(
                lp.isArabic ? "تحقق من الأمان" : "Vérification de sécurité",
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: primaryColor),
              ),
              const SizedBox(height: 12),
              Text(
                lp.isArabic 
                    ? "أدخل الرمز المكون من 6 أرقام المرسل إلى\n$displayContact"
                    : "Entrez le code à 6 chiffres envoyé au\n$displayContact",
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 16, color: Colors.grey, height: 1.5),
              ),
              const SizedBox(height: 48),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: List.generate(6, (index) {
                  return SizedBox(
                    width: 45,
                    child: TextField(
                      controller: _controllers[index],
                      focusNode: _focusNodes[index],
                      keyboardType: TextInputType.number,
                      textAlign: TextAlign.center,
                      maxLength: 1,
                      style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                      decoration: InputDecoration(
                        counterText: "",
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: Colors.grey),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: primaryColor, width: 2),
                        ),
                      ),
                      onChanged: (value) {
                        if (value.isNotEmpty && index < 5) {
                          _focusNodes[index + 1].requestFocus();
                        } else if (value.isEmpty && index > 0) {
                          _focusNodes[index - 1].requestFocus();
                        }
                        if (codeComplete) {
                          _verifyOtp();
                        }
                      },
                    ),
                  );
                }),
              ),
              const SizedBox(height: 48),
              Text(
                _formatTime(_secondsRemaining),
                style: TextStyle(
                  fontSize: 18, 
                  fontWeight: FontWeight.bold, 
                  color: _secondsRemaining < 30 ? Colors.red : primaryColor
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 55,
                child: ElevatedButton(
                  onPressed: _isLoading || !codeComplete ? null : _verifyOtp,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: primaryColor,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    elevation: 0,
                  ),
                  child: _isLoading 
                      ? const CircularProgressIndicator(color: Colors.white) 
                      : Text(lp.isArabic ? "تأكيد" : "Vérifier", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(height: 24),
              TextButton(
                onPressed: _secondsRemaining == 0 ? _resendOtp : null,
                child: Text(
                  lp.isArabic ? "إعادة إرسال الرمز" : "Renvoyer le code",
                  style: TextStyle(
                    color: _secondsRemaining == 0 ? primaryColor : Colors.grey,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  bool get codeComplete => _controllers.every((c) => c.text.isNotEmpty);
}

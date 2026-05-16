import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:mobile_app/services/api_service.dart';
import 'package:mobile_app/screens/pdf_viewer_screen.dart';
import 'package:flutter/foundation.dart';
import 'dart:io' as dart_io;
import 'package:intl/intl.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:mobile_app/widgets/completion_dialog.dart';
import 'package:provider/provider.dart';
import 'package:mobile_app/providers/language_provider.dart';

/// ── Constantes de design (Style Gemini Moderne) ──────────────────────────────
const kPrimaryColor = Color(0xFF1A237E);
const kNavy = Color(0xFF1A237E); // Ajout de la constante kNavy manquante
const kBgLight = Color(0xFFF1F4F9); // Fond Gemini Authentique
const kWhite = Colors.white;
const kUserBubble = Color(0xFFE7F0FF);
const kAiBubble = Colors.white;
const kAccentColor = Color(0xFFC5A059);

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with TickerProviderStateMixin {
  final List<Map<String, dynamic>> _messages = [];
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final ImagePicker _picker = ImagePicker();
  final AudioRecorder _audioRecorder = AudioRecorder();

  int? _currentSessionId;
  List<dynamic> _sessions = [];
  bool _isLoadingSessions = false;
  bool _isSending = false;
  bool _isRecording = false;
  
  final TextEditingController _sessionSearchController = TextEditingController();
  String _sessionSearchQuery = "";

  XFile? _vendeurFile;
  XFile? _acheteurFile;
  XFile? _carteGriseFront;
  XFile? _carteGriseBack;
  XFile? _permisOccuper;
  String _selectedActType = "vente_immobilier";
  
  // Nouveaux états pour le flux guidé
  int? _activeDocumentId;
  bool _isWaitingForPrice = false;
  String? _waitingForHypothequeField; // 'montant', 'duree', 'conditions'
  int _currentStep = 0;


  @override
  void initState() {
    super.initState();
    _loadSessions();
  }

  @override
  void dispose() {
    _audioRecorder.dispose();
    _scrollController.dispose();
    _controller.dispose();
    _sessionSearchController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _loadSessions() async {
    setState(() => _isLoadingSessions = true);
    try {
      final sessions = await ApiService.getChatSessions();
      setState(() {
        _sessions = sessions;
        if (_sessions.isNotEmpty && _currentSessionId == null) {
          _loadMessages(_sessions.first['id']);
        } else if (_sessions.isEmpty) {
          _startNewSession();
        }
      });
    } catch (e) {
      if (kDebugMode) print("Error loading sessions: $e");
    } finally {
      setState(() => _isLoadingSessions = false);
    }
  }

  Future<void> _loadMessages(int sessionId) async {
    setState(() {
      _currentSessionId = sessionId;
      _messages.clear();
    });
    try {
      final messages = await ApiService.getChatMessages(sessionId);
      setState(() {
        for (var m in messages) {
          _messages.add({
            "text": m['content'],
            "isUser": m['role'] == 'user',
            "type": m['message_type'],
            "time": m['created_at'] != null
                ? DateTime.parse(m['created_at'])
                : DateTime.now(),
          });
        }
      });
      _scrollToBottom();
    } catch (e) {
      if (kDebugMode) print("Error loading messages: $e");
    }
  }

  void _resetActState() {
    setState(() {
      _vendeurFile = null;
      _acheteurFile = null;
      _carteGriseFront = null;
      _carteGriseBack = null;
      _permisOccuper = null;
      _currentStep = 0;
      _activeDocumentId = null;
      _isWaitingForPrice = false;
      _waitingForHypothequeField = null;
    });
  }

  Future<void> _startNewSession() async {
    try {
      final session = await ApiService.createChatSession();
      setState(() {
        _currentSessionId = session['id'];
        _messages.clear();
      });
      _resetActState();
      _loadSessions();
    } catch (e) {
      if (kDebugMode) print("Error creating session: $e");
    }
  }

  /// Envoie une réponse vers Gemini et affiche la réponse IA réelle.
  Future<void> _sendMessage(String text) async {
    final time = DateTime.now();
    
    // CAS PARTICULIER : Intercepter le prix dans le flux guidé (Véhicule)
    if (_isWaitingForPrice && _activeDocumentId != null) {
      setState(() {
        _messages.add({"text": text, "isUser": true, "time": time});
        _isSending = true;
        _isWaitingForPrice = false;
      });
      _controller.clear();
      _scrollToBottom();
      try {
        final lp = Provider.of<LanguageProvider>(context, listen: false);
        final lang = lp.currentLocale.languageCode;
        final completed = await ApiService.completeAct(_activeDocumentId!, {"prix": text}, lang);
        final newStatus = completed['status'] ?? 'brouillon';
        final newPdfUrl = ApiService.getFullUrl(completed['pdf_url'] ?? '');

        
        setState(() {
          String successKey = 'price_saved';
          if (_selectedActType == 'vente_immobilier') {
            successKey = 'price_saved_immobilier';
          }
          
          _messages.add({
            "text": newStatus == 'valide'
                ? lp.translate(successKey).replaceFirst('{price}', text)
                : lp.translate('act_updated_missing'),
            "isUser": false,
            "pdfUrl": newPdfUrl,
            "documentId": _activeDocumentId,
            "time": DateTime.now()
          });
          _activeDocumentId = null;
        });
        _scrollToBottom();
      } catch (e) {
        final lp = Provider.of<LanguageProvider>(context, listen: false);
        setState(() {
          _messages.add({"text": "❌ ${lp.isArabic ? 'خطأ في السعر' : 'Erreur prix'} : $e", "isUser": false, "time": DateTime.now()});
          _isWaitingForPrice = true;
        });
      } finally {
        setState(() => _isSending = false);
      }
      return;
    }


    // CAS PARTICULIER : Intercepter les champs Hypothèque (Flux Guidé)
    if (_waitingForHypothequeField != null && _activeDocumentId != null) {
      setState(() {
        _messages.add({"text": text, "isUser": true, "time": time});
        _isSending = true;
      });
      _controller.clear();
      _scrollToBottom();

      try {
        Map<String, String> data = {};
        String nextField = "";
        String nextQuestion = "";

        final lp = Provider.of<LanguageProvider>(context, listen: false);
        if (_waitingForHypothequeField == 'montant') {
          data = {"montant_dette": text};
          nextField = "duree";
          nextQuestion = lp.translate('hypotheque_step2');
        } else if (_waitingForHypothequeField == 'duree') {
          data = {"duree_remboursement": text};
          nextField = "conditions";
          nextQuestion = lp.translate('hypotheque_step3');
        } else if (_waitingForHypothequeField == 'conditions') {
          data = {"conditions_execution": text};
          nextField = "done";
          nextQuestion = lp.translate('hypotheque_final');
        }


        final lang = Provider.of<LanguageProvider>(context, listen: false).currentLocale.languageCode;
        final completed = await ApiService.completeAct(_activeDocumentId!, data, lang);
        final newPdfUrl = ApiService.getFullUrl(completed['pdf_url'] ?? '');
        final remaining = List<String>.from(completed['missing_fields'] ?? []);


        setState(() {
          if (nextField == "done" || remaining.isEmpty) {
            _messages.add({
              "text": nextQuestion,
              "isUser": false,
              "pdfUrl": newPdfUrl,
              "documentId": _activeDocumentId,
              "time": DateTime.now()
            });
            _waitingForHypothequeField = null;
            _activeDocumentId = null;
          } else {
            _messages.add({
              "text": lp.translate('field_saved').replaceFirst('{next}', nextQuestion),
              "isUser": false,
              "time": DateTime.now()
            });
            _waitingForHypothequeField = nextField;
          }
        });

        _scrollToBottom();
      } catch (e) {
        setState(() {
          _messages.add({"text": "❌ Erreur : $e", "isUser": false, "time": DateTime.now()});
        });
      } finally {
        setState(() => _isSending = false);
      }
      return;
    }

    final lowerText = text.toLowerCase();
    bool typeDetected = false;
    String? newType;

    if (lowerText.contains("mariage") || lowerText.contains("عقد") || lowerText.contains("زواج")) {
      newType = "mariage";
      typeDetected = true;
    } else if (lowerText.contains("véhicule") || lowerText.contains("vehicule") || lowerText.contains("voiture") || lowerText.contains("سيارة") || lowerText.contains("مركبة")) {
      newType = "vente_vehicule";
      typeDetected = true;
    } else if (lowerText.contains("société") || lowerText.contains("societe") || lowerText.contains("parts") || lowerText.contains("شركة") || lowerText.contains("حصص")) {
      newType = "vente_societe";
      typeDetected = true;
    } else if (lowerText.contains("immobilier") || lowerText.contains("terrain") || lowerText.contains("maison") || lowerText.contains("عقار") || lowerText.contains("أرض") || lowerText.contains("بيع")) {
      newType = "vente_immobilier";
      typeDetected = true;
    } else if (lowerText.contains("testament") || lowerText.contains("testement") || lowerText.contains("legs") || lowerText.contains("وصية")) {
      newType = "testament";
      typeDetected = true;
    } else if (lowerText.contains("hypothèque") || lowerText.contains("hypotheque") || lowerText.contains("créance") || lowerText.contains("رهن")) {
      newType = "hypotheque";
      typeDetected = true;
    }

    if (typeDetected && newType != null) {
      if (newType != _selectedActType) {
        _resetActState();
        _selectedActType = newType;
      }
    }


     // final time already declared above

    setState(() {
      _messages.add({"text": text, "isUser": true, "time": time});
      _isSending = true;
    });
    _controller.clear();
    _scrollToBottom();

    try {
      final lang = Provider.of<LanguageProvider>(context, listen: false).currentLocale.languageCode;
      final result = await ApiService.sendAiMessage(_currentSessionId!, text, lang);

      final aiText = result['reply'] as String? ?? "Je traite votre demande…";
      final detectedActType = result['detected_act_type'] as String?;

      setState(() {
        _messages.add({"text": aiText, "isUser": false, "time": DateTime.now()});
        if (detectedActType != null) {
          if (detectedActType != _selectedActType) {
            _resetActState();
            _selectedActType = detectedActType;
          }
          if (kDebugMode) print("DEBUG: Detected Act Type from backend: $_selectedActType");
        }
      });
      _scrollToBottom();
    } catch (e) {
      setState(() {
        _messages.add({
          "text": "⚠ Erreur de communication : $e",
          "isUser": false,
          "time": DateTime.now()
        });
      });
    } finally {
      setState(() => _isSending = false);
    }
  }

  Future<void> _toggleRecording() async {
    if (_isRecording) {
      final path = await _audioRecorder.stop();
      setState(() => _isRecording = false);
      if (path != null) {
        setState(() {
          _messages.add({
            "text": "🎤 Message vocal envoyé",
            "isUser": true,
            "time": DateTime.now()
          });
        });
        try {
          final res = await ApiService.sendVoiceMessage(path);
          final transcription = res['transcription'] ?? "Transcription indisponible";
          // Envoyer la transcription comme message chat vers Gemini
          await _sendMessage(transcription);
        } catch (e) {
          setState(() {
            _messages.add({
              "text": "Erreur transcription vocal : $e",
              "isUser": false,
              "time": DateTime.now()
            });
          });
        }
      }
    } else {
      if (kIsWeb) {
        // Sur le web, l'enregistrement audio n'est pas supporté simplement
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Enregistrement vocal non disponible sur web.")),
        );
        return;
      }
      if (await Permission.microphone.request().isGranted) {
        final directory = await getApplicationDocumentsDirectory();
        final path =
            '${directory.path}/recording_${DateTime.now().millisecondsSinceEpoch}.m4a';
        await _audioRecorder.start(const RecordConfig(), path: path);
        setState(() => _isRecording = true);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text("🔴 Enregistrement en cours…"),
              duration: Duration(seconds: 2)),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Permission microphone refusée")),
        );
      }
    }
  }

  Future<void> _pickImage(ImageSource source) async {
    final XFile? imageFile = await _picker.pickImage(source: source);
    if (imageFile == null) return;

    final lp = Provider.of<LanguageProvider>(context, listen: false);

    // 1. Déterminer le label en fonction du type d'acte
    String p1 = lp.isArabic ? "الطرف 1" : "Partie 1";
    String p2 = lp.isArabic ? "الطرف 2" : "Partie 2";

    if (_selectedActType == "mariage") {
      p1 = lp.translate("husband");
      p2 = lp.translate("wife");
    } else if (_selectedActType == "vente_immobilier" || _selectedActType == "vente_vehicule" || _selectedActType == "vente_societe") {
      p1 = lp.translate("seller");
      p2 = lp.translate("buyer");
    } else if (_selectedActType == "testament") {
      p1 = lp.translate("testator");
      p2 = lp.translate("beneficiary");
    } else if (_selectedActType == "hypotheque") {
      p1 = lp.translate("debtor");
      p2 = lp.translate("creditor");
    }

    if (_currentStep == 0) {
      // Envoi CI 1
      setState(() {
        _vendeurFile = imageFile;
        _messages.add({
          "role": "user",
          "isUser": true,
          "text": lp.translate('id_sent_p1').replaceFirst('{label}', p1),
          "image": imageFile.path,
          "time": DateTime.now()
        });
      });
      _scrollToBottom();
      await Future.delayed(const Duration(seconds: 1));
      setState(() {
        _messages.add({
          "role": "assistant",
          "isUser": false,
          "text": lp.translate('id_received_p1').replaceFirst('{label}', p1).replaceFirst('{label2}', p2),
          "time": DateTime.now()
        });
        _currentStep = 1;
      });
    } else if (_currentStep == 1) {
      // Envoi CI 2
      setState(() {
        _acheteurFile = imageFile;
        _messages.add({
          "role": "user",
          "isUser": true,
          "text": lp.translate('id_sent_p2').replaceFirst('{label}', p2),
          "image": imageFile.path,
          "time": DateTime.now()
        });
      });
      _scrollToBottom();
      await Future.delayed(const Duration(seconds: 1));

      if (_selectedActType == "vente_vehicule") {
        setState(() {
          _messages.add({
            "role": "assistant",
            "isUser": false,
            "text": lp.translate('send_carte_grise_recto'),
            "time": DateTime.now()
          });
          _currentStep = 2;
        });
      } else if (_selectedActType == "vente_immobilier" || _selectedActType == "hypotheque") {
        setState(() {
          _messages.add({
            "role": "assistant",
            "isUser": false,
            "text": lp.translate('send_permis_occuper').replaceFirst('{label}', p2),
            "time": DateTime.now()
          });
          _currentStep = 2;
        });
      } else {
        // Pour les autres actes, on génère directement après les 2 CI
        String typeTranslated = lp.translate(_selectedActType ?? 'notarial_act');
        setState(() {
          _messages.add({
            "role": "assistant",
            "isUser": false,
            "text": lp.translate('analyzing_ids').replaceFirst('{type}', typeTranslated),
            "time": DateTime.now()
          });
        });
        _processIdCards();
      }
    } else if (_currentStep == 2 && _selectedActType == "vente_vehicule") {
      // Envoi Carte Grise Recto
      setState(() {
        _carteGriseFront = imageFile;
        _messages.add({
          "role": "user",
          "isUser": true,
          "text": lp.translate('cg_recto_sent'),
          "image": imageFile.path,
          "time": DateTime.now()
        });
      });
      _scrollToBottom();
      await Future.delayed(const Duration(seconds: 1));
      setState(() {
        _messages.add({
          "role": "assistant",
          "isUser": false,
          "text": lp.translate('send_cg_verso'),
          "time": DateTime.now()
        });
        _currentStep = 3;
      });
    } else if (_currentStep == 3 && _selectedActType == "vente_vehicule") {
      // Envoi Carte Grise Verso
      setState(() {
        _carteGriseBack = imageFile;
        _messages.add({
          "role": "user",
          "isUser": true,
          "text": lp.translate('cg_verso_sent'),
          "image": imageFile.path,
          "time": DateTime.now()
        });
      });
      _scrollToBottom();
      await Future.delayed(const Duration(seconds: 1));
      setState(() {
        _messages.add({
          "role": "assistant",
          "isUser": false,
          "text": lp.translate('all_pieces_received'),
          "time": DateTime.now()
        });
      });
      _processIdCards();
    } else if (_currentStep == 2 && (_selectedActType == "vente_immobilier" || _selectedActType == "hypotheque")) {
      // Envoi Permis d'occuper
      setState(() {
        _permisOccuper = imageFile;
        _messages.add({
          "role": "user",
          "isUser": true,
          "text": lp.translate('permis_sent'),
          "image": imageFile.path,
          "time": DateTime.now()
        });
      });
      _scrollToBottom();
      await Future.delayed(const Duration(seconds: 1));
      setState(() {
        _messages.add({
          "role": "assistant",
          "isUser": false,
          "text": lp.translate('permis_received'),
          "time": DateTime.now()
        });
      });
      _processIdCards();
    }
    _scrollToBottom();
  }

  Future<void> _processIdCards() async {
    setState(() => _isSending = true);
    
    if (_vendeurFile == null || _acheteurFile == null) {
      setState(() {
        final lp = Provider.of<LanguageProvider>(context, listen: false);
        _messages.add({
          "text": "⚠ Erreur : Les cartes d'identité sont manquantes. Veuillez recommencer le scan.",
          "isUser": false,
          "time": DateTime.now()
        });
        _isSending = false;
        _currentStep = 0;
      });
      return;
    }

    try {
      final lang = Provider.of<LanguageProvider>(context, listen: false).currentLocale.languageCode;
      final res = await ApiService.sendIdCards(
        _vendeurFile!, 
        _acheteurFile!, 
        actType: _selectedActType,
        carteGriseFront: _carteGriseFront,
        carteGriseBack: _carteGriseBack,
        permisOccuper: _permisOccuper,
        lang: lang,
      );
      
      final parties = res['parties_extrait'] ?? {};
      final isMariage = _selectedActType == "mariage";
      final isTestament = _selectedActType == "testament";
      final isHypotheque = _selectedActType == "hypotheque";
      
      final p1Nom = isMariage ? (parties['monsieur']?['nom'] ?? '—') : (isTestament ? (parties['testateur']?['nom'] ?? '—') : (isHypotheque ? (parties['debiteur']?['nom'] ?? '—') : (parties['vendeur']?['nom'] ?? '—')));
      final p2Nom = isMariage ? (parties['madame']?['nom'] ?? '—') : (isTestament ? (parties['beneficiaire']?['nom'] ?? '—') : (isHypotheque ? (parties['creancier']?['nom'] ?? '—') : (parties['acheteur']?['nom'] ?? '—')));
      
      final lp = Provider.of<LanguageProvider>(context, listen: false);
      String typeTranslated = lp.translate(_selectedActType ?? 'notarial_act');
      
      String p1Label = "Partie 1";
      String p2Label = "Partie 2";
      if (_selectedActType == "mariage") {
        p1Label = lp.translate("husband");
        p2Label = lp.translate("wife");
      } else if (_selectedActType == "vente_immobilier" || _selectedActType == "vente_vehicule" || _selectedActType == "vente_societe") {
        p1Label = lp.translate("seller");
        p2Label = lp.translate("buyer");
      } else if (_selectedActType == "testament") {
        p1Label = lp.translate("testator");
        p2Label = lp.translate("beneficiary");
      } else if (_selectedActType == "hypotheque") {
        p1Label = lp.translate("debtor");
        p2Label = lp.translate("creditor");
      }
      
      final docId = res['document_id'] as int?;
      final pdfUrl = ApiService.getFullUrl(res['pdf_url'] ?? '');
      final missingFields = List<String>.from(res['missing_fields'] ?? []);

      setState(() {
        _activeDocumentId = docId;
        _messages.add({
          "text": lp.translate('act_generated_success')
              .replaceFirst('{type}', typeTranslated)
              .replaceFirst('{label1}', p1Label)
              .replaceFirst('{name1}', p1Nom)
              .replaceFirst('{label2}', p2Label)
              .replaceFirst('{name2}', p2Nom),
          "isUser": false,
          "pdfUrl": pdfUrl,
          "documentId": docId,
          "missingFields": missingFields,
          "time": DateTime.now()
        });
        
        // Réinitialisation des fichiers
        _vendeurFile = null;
        _acheteurFile = null;
        _carteGriseFront = null;
        _carteGriseBack = null;
        _permisOccuper = null;
      });
      _scrollToBottom();

      // Flux spécifique pour la vente de véhicule
      if (_selectedActType == "vente_vehicule" && docId != null) {
        if (missingFields.any((f) => f.contains("Prix"))) {
          setState(() => _isWaitingForPrice = true);
          await Future.delayed(const Duration(milliseconds: 700));
          setState(() {
            _messages.add({
              "text": lp.translate('ask_price_vehicule'),
              "isUser": false,
              "time": DateTime.now()
            });
          });
          _scrollToBottom();
          return;
        }
      }

      // Flux spécifique pour la vente immobilière
      if (_selectedActType == "vente_immobilier" && docId != null) {
        if (missingFields.any((f) => f.contains("Prix") || f.contains("prix"))) {
          setState(() => _isWaitingForPrice = true);
          await Future.delayed(const Duration(milliseconds: 700));
          setState(() {
            _messages.add({
              "text": lp.translate('ask_price_immobilier'),
              "isUser": false,
              "time": DateTime.now()
            });
          });
          _scrollToBottom();
          return;
        }
      }

      // Flux spécifique pour l'hypothèque
      if (_selectedActType == "hypotheque" && docId != null) {
        if (missingFields.isNotEmpty) {
          setState(() => _waitingForHypothequeField = 'montant');
          await Future.delayed(const Duration(milliseconds: 700));
          setState(() {
            _messages.add({
              "text": lp.translate('hypotheque_step1'),
              "isUser": false,
              "time": DateTime.now()
            });
          });
          _scrollToBottom();
          return;
        }
      }

      if (missingFields.isNotEmpty && docId != null && 
          _selectedActType != "vente_immobilier" && 
          _selectedActType != "hypotheque") {
        await Future.delayed(const Duration(milliseconds: 700));
        if (mounted) {
          await _showCompletionDialog(docId, missingFields, pdfUrl);
        }
      }

      if (_currentSessionId != null) {
        await ApiService.addChatMessage(
            _currentSessionId!,
            "assistant",
            lp.translate('draft_generated_log')
                .replaceFirst('{p1}', p1Label)
                .replaceFirst('{name1}', p1Nom)
                .replaceFirst('{p2}', p2Label)
                .replaceFirst('{name2}', p2Nom),
            "pdf");
      }
    } catch (e) {
      setState(() {
        final lp = Provider.of<LanguageProvider>(context, listen: false);
        _messages.add({
          "text": lp.translate('generation_error').replaceFirst('{error}', e.toString()),
          "isUser": false,
          "time": DateTime.now()
        });
        _vendeurFile = null;
        _acheteurFile = null;
        _carteGriseFront = null;
        _carteGriseBack = null;
        _permisOccuper = null;
      });
    } finally {
      setState(() => _isSending = false);
    }
  }

  /// Dialogue interactif pour compléter les champs manquants de l'acte.
  Future<void> _showCompletionDialog(
      int docId, List<String> missingFields, String oldPdfUrl) async {
    final fieldKeys = CompletionDialog.getFieldKeys();
    final Map<String, TextEditingController> controllers = {};
    for (final field in missingFields) {
      if (fieldKeys.containsKey(field)) {
        controllers[field] = TextEditingController();
      }
    }

    if (controllers.isEmpty) return;

    setState(() {
      final lp = Provider.of<LanguageProvider>(context, listen: false);
      String msg = lp.translate('completion_needed').replaceFirst('{count}', controllers.length.toString());
      
      if (_selectedActType == "vente_vehicule" && missingFields.any((f) => f.contains("Prix"))) {
        msg = lp.translate('cg_extracted_price_needed');
      }

      _messages.add({
        "text": msg,
        "isUser": false,
        "time": DateTime.now()
      });
    });


    final result = await showDialog<Map<String, String>>(
      context: context,
      barrierDismissible: false,
      builder: (context) => CompletionDialog(
        controllers: controllers,
        fieldKeys: fieldKeys,
        missingFields: missingFields,
        actType: _selectedActType,
      ),
    );

    if (result != null && result.isNotEmpty) {
      final details = result.entries.map((e) => "• ${e.key} : ${e.value}").join("\n");
      setState(() {
        _messages.add({
          "text": "📋 Informations complétées :\n$details\n\nRégénération en cours…",
          "isUser": true,
          "time": DateTime.now()
        });
        _isSending = true;
      });
      _scrollToBottom();

      try {
        final lp = Provider.of<LanguageProvider>(context, listen: false);
        final lang = lp.currentLocale.languageCode;
        final completed = await ApiService.completeAct(docId, result, lang);
        final newStatus = completed['status'] ?? 'brouillon';
        final newPdfUrl = ApiService.getFullUrl(completed['pdf_url'] ?? '');
        final remaining =
            List<String>.from(completed['missing_fields'] ?? []);

        setState(() {
          _messages.add({
            "text": newStatus == 'valide'
                ? lp.translate('finalized_act')
                : lp.translate('act_updated_missing'),
            "isUser": false,
            "pdfUrl": newPdfUrl,
            "documentId": docId,
            "missingFields": remaining,
            "time": DateTime.now()
          });
        });
        _scrollToBottom();
      } catch (e) {
        setState(() {
          _messages.add({
            "text": "❌ Erreur : $e",
            "isUser": false,
            "time": DateTime.now()
          });
        });
      } finally {
        setState(() => _isSending = false);
      }
    } else {
      setState(() {
        final lp = Provider.of<LanguageProvider>(context, listen: false);
        _messages.add({
          "text": lp.translate('form_cancelled'),
          "isUser": false,
          "pdfUrl": oldPdfUrl,
          "documentId": docId,
          "missingFields": missingFields,
          "time": DateTime.now()
        });
      });
    }
  }

  void _handleLogout() {
    final lp = Provider.of<LanguageProvider>(context, listen: false);
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

  void _showAttachmentMenu() {
    final lp = Provider.of<LanguageProvider>(context, listen: false);
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Wrap(
            children: [
              ListTile(
                leading: const Icon(Icons.camera_alt, color: kNavy),
                title: Text(lp.isArabic ? "الكاميرا" : "Appareil photo"),
                subtitle: Text(lp.isArabic ? "بطاقة الهوية مباشرة" : "Carte d\'identité en direct"),
                onTap: () {
                  Navigator.pop(context);
                  _pickImage(ImageSource.camera);
                },
              ),
              ListTile(
                leading: const Icon(Icons.photo_library, color: kNavy),
                title: Text(lp.isArabic ? "معرض الصور" : "Galerie photo"),
                subtitle: Text(lp.isArabic ? "اختر من الألبوم" : "Sélectionner depuis l\'album"),
                onTap: () {
                  Navigator.pop(context);
                  _pickImage(ImageSource.gallery);
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showActTypeSelection(LanguageProvider lp) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => Container(
        padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(lp.translate('act_type_q'),
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 20),
              _buildActOption(Icons.home_work_outlined, lp.translate('immobilier'), "vente_immobilier"),
              _buildActOption(Icons.directions_car_outlined, lp.translate('vehicule'), "vente_vehicule"),
              _buildActOption(Icons.business_outlined, lp.translate('societe'), "vente_societe"),
              _buildActOption(Icons.favorite_outline, lp.translate('mariage'), "mariage"),
              _buildActOption(Icons.menu_book_outlined, lp.translate('testament'), "testament"),
              _buildActOption(Icons.security_outlined, lp.translate('hypotheque'), "hypotheque"),
              const SizedBox(height: 10),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActOption(IconData icon, String title, String code) {
    final lp = Provider.of<LanguageProvider>(context, listen: false);
    return ListTile(
      leading: Icon(icon, color: kNavy),
      title: Text(title),
      onTap: () {
        Navigator.pop(context);
        setState(() {
          _selectedActType = code;
          _vendeurFile = null;
          _acheteurFile = null;
          _carteGriseFront = null;
          _carteGriseBack = null;
          _permisOccuper = null;
          _activeDocumentId = null;
          _isWaitingForPrice = false;
          
          final isMariage = code == "mariage";
          final isTestament = code == "testament";
          final isHypotheque = code == "hypotheque";
          
          String label;
          if (isMariage) {
            label = lp.translate('husband');
          } else if (isTestament) {
            label = lp.translate('testator');
          } else if (isHypotheque) {
            label = lp.translate('debtor');
          } else {
            label = lp.translate('seller');
          }

          _messages.add({
            "text": lp.translate('start_chat_title').replaceFirst('{title}', title),
            "isUser": true,
            "time": DateTime.now()
          });
          _messages.add({
            "text": lp.translate('start_chat_id_request').replaceFirst('{label}', label),
            "isUser": false,
            "time": DateTime.now()
          });
        });
        _scrollToBottom();
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final lp = Provider.of<LanguageProvider>(context);
    final notaryName = ApiService.notaryName ?? lp.translate('welcome_back');

    return Scaffold(
      backgroundColor: Colors.white,
      drawer: _buildDrawer(lp),
      appBar: _buildAppBar(lp),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? _buildWelcomeScreen(notaryName, lp)
                : _buildMessageList(lp),
          ),
          if (_isSending) _buildTypingIndicator(),
          _buildInputBar(lp),
        ],
      ),
    );
  }

  PreferredSizeWidget _buildAppBar(LanguageProvider lp) {
    return AppBar(
      elevation: 0,
      backgroundColor: Colors.transparent,
      iconTheme: const IconThemeData(color: Colors.black87),
      title: const SizedBox.shrink(), // Le titre est dans l'écran d'accueil
      centerTitle: true,
      actions: [
        TextButton.icon(
          onPressed: () => lp.toggleLanguage(),
          icon: const Icon(Icons.language, color: kNavy, size: 20),
          label: Text(
            lp.isArabic ? "FR" : "AR",
            style: const TextStyle(color: kNavy, fontWeight: FontWeight.bold, fontSize: 13),
          ),
        ),
        Padding(
          padding: const EdgeInsets.only(right: 8.0, left: 8.0),
          child: InkWell(
            onTap: () => Navigator.pushNamed(context, '/profile'),
            child: Container(
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: Colors.black12, width: 1),
              ),
              child: CircleAvatar(
                radius: 18,
                backgroundColor: Colors.grey[200],
                backgroundImage: const NetworkImage("https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildDrawer(LanguageProvider lp) {
    return Drawer(
      child: Column(
        children: [
          UserAccountsDrawerHeader(
            decoration: const BoxDecoration(color: kNavy),
            accountName: Text(ApiService.notaryName ?? lp.translate('welcome_back'),
                style: const TextStyle(fontWeight: FontWeight.bold)),
            accountEmail: Text(lp.isArabic ? "موثق محترف" : "Professionnel du droit",
                style: const TextStyle(fontSize: 12)),
            currentAccountPicture: const CircleAvatar(
                backgroundColor: kWhite,
                child: Icon(Icons.gavel, color: kNavy, size: 30)),
          ),
          ListTile(
            leading: const Icon(Icons.add_comment_outlined, color: kNavy),
            title: Text(lp.translate('new_chat')),
            onTap: () {
              Navigator.pop(context);
              _startNewSession();
            },
          ),

          ListTile(
            leading:
                const Icon(Icons.folder_outlined, color: kNavy),
            title: Text(lp.translate('my_acts')),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/documents');
            },
          ),
          ListTile(
            leading: const Icon(Icons.search_outlined, color: kNavy),
            title: Text(lp.translate('search_filter')),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/search');
            },
          ),
          if (ApiService.isAdmin)
            ListTile(
              leading: const Icon(Icons.people_outline, color: kNavy),
              title: Text(lp.translate('manage_users')),
              onTap: () {
                Navigator.pop(context);
                Navigator.pushNamed(context, '/admin/users');
              },
            ),
          const Divider(),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(children: [
              const Icon(Icons.history, size: 14, color: Colors.grey),
              const SizedBox(width: 6),
              Text(lp.translate('history_title'),
                  style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: Colors.grey,
                      letterSpacing: 0.5)),
            ]),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 5),
            child: TextField(
              controller: _sessionSearchController,
              onChanged: (value) {
                setState(() {
                  _sessionSearchQuery = value.toLowerCase();
                });
              },
              decoration: InputDecoration(
                hintText: lp.translate('search_chat_hint'),
                hintStyle: const TextStyle(fontSize: 13),
                prefixIcon: const Icon(Icons.search, size: 18),
                isDense: true,
                contentPadding: const EdgeInsets.symmetric(vertical: 8),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide(color: Colors.grey.shade300),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide(color: Colors.grey.shade200),
                ),
              ),
            ),
          ),
          Expanded(
            child: _isLoadingSessions
                ? const Center(child: CircularProgressIndicator())
                : Builder(
                    builder: (context) {
                      final filteredSessions = _sessions.where((s) {
                        return s['title'].toString().toLowerCase().contains(_sessionSearchQuery);
                      }).toList();

                      if (filteredSessions.isEmpty && _sessionSearchQuery.isNotEmpty) {
                        return Center(child: Text(lp.translate('no_results'), style: const TextStyle(fontSize: 12, color: Colors.grey)));
                      }

                      return ListView.builder(
                        itemCount: filteredSessions.length,
                        itemBuilder: (context, index) {
                          final s = filteredSessions[index];
                          final isCurrent = s['id'] == _currentSessionId;
                          return ListTile(
                            leading: Icon(Icons.chat_bubble_outline,
                                size: 16,
                                color: isCurrent ? kNavy : Colors.grey),
                            title: Text(s['title'],
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                    fontSize: 13,
                                    color: isCurrent ? kNavy : null,
                                    fontWeight: isCurrent
                                        ? FontWeight.bold
                                        : FontWeight.normal)),
                            subtitle: Text(
                              DateFormat('dd/MM HH:mm')
                                  .format(DateTime.parse(s['created_at'])),
                              style: const TextStyle(fontSize: 11),
                            ),
                            selected: isCurrent,
                            selectedTileColor: kNavy.withOpacity(0.05),
                            onTap: () {
                              Navigator.pop(context);
                              _loadMessages(s['id']);
                            },
                          );
                        },
                      );
                    },
                  ),
          ),

        ],
      ),
    );
  }

  Widget _buildWelcomeScreen(String name, LanguageProvider lp) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 10),
            Text("${lp.translate('welcome_back')} $name,",
                style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.w400,
                    color: Colors.black54)),
            Text(lp.translate('start_where'),
                style: const TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87)),
            const SizedBox(height: 30),
            _buildActionCard(
              Icons.camera_alt_outlined,
              lp.translate('generate_act'),
              lp.translate('generate_act_desc'),
              onTap: () => _showActTypeSelection(lp),
              badgeText: "IA",
            ),
            _buildActionCard(
              Icons.description_outlined,
              lp.translate('view_docs'),
              lp.translate('view_docs_desc'),
              onTap: () => Navigator.pushNamed(context, '/documents'),
            ),
            _buildActionCard(
              Icons.gavel_outlined,
              lp.translate('legal_advice'),
              lp.translate('legal_advice_desc'),
              onTap: () =>
                  _sendMessage(lp.isArabic ? "مرحباً يا أستاذ، كيف يمكنني مساعدتك؟" : "Bonjour Maître, comment puis-je vous aider ?"),
              badgeText: "Gemini",
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionCard(IconData icon, String title, String subtitle,
      {VoidCallback? onTap, String? badgeText}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
        border: Border.all(color: Colors.black.withOpacity(0.05)),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
          child: Row(
            children: [
              Icon(icon, color: Colors.black87, size: 22),
              const SizedBox(width: 16),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    fontWeight: FontWeight.w500,
                    fontSize: 15,
                    color: Colors.black87,
                  ),
                ),
              ),
              const Icon(Icons.arrow_forward_ios_rounded, color: Colors.black26, size: 14),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMessageList(LanguageProvider lp) {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.fromLTRB(12, 16, 12, 8),
      itemCount: _messages.length,
      itemBuilder: (context, index) {
        final msg = _messages[index];
        return _ChatBubble(
          text: msg["text"],
          imagePath: msg["image"],
          isUser: msg["isUser"] ?? false,
          pdfUrl: msg["pdfUrl"],
          documentId: msg["documentId"],
          missingFields: msg["missingFields"] != null ? List<String>.from(msg["missingFields"]) : null,
          time: msg["time"],
          actType: _selectedActType,
          lp: lp,
        );
      },
    );
  }

  Widget _buildTypingIndicator() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      alignment: Alignment.centerLeft,
      child: Row(
        children: [
          const CircleAvatar(
              radius: 14,
              backgroundColor: kNavy,
              child: Icon(Icons.auto_awesome, size: 12, color: Colors.white)),
          const SizedBox(width: 10),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
                color: kWhite,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                      color: Colors.black.withOpacity(0.04),
                      blurRadius: 6)
                ]),
            child: const Row(
              children: [
                _TypingDot(delay: 0),
                SizedBox(width: 4),
                _TypingDot(delay: 200),
                SizedBox(width: 4),
                _TypingDot(delay: 400),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputBar(LanguageProvider lp) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      decoration: const BoxDecoration(color: Colors.transparent),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: const Color(0xFFE9EEF6), // Fond capsule Gemini
          borderRadius: BorderRadius.circular(30),
        ),
        child: Row(
          children: [
            IconButton(
              icon: const Icon(Icons.add, color: Colors.black54),
              onPressed: _showAttachmentMenu,
            ),
            IconButton(
              icon: const Icon(Icons.tune_rounded, color: Colors.black54),
              onPressed: () => Navigator.pushNamed(context, '/search'),
            ),
            Expanded(
              child: TextField(
                controller: _controller,
                textAlign: lp.isArabic ? TextAlign.right : TextAlign.left,
                decoration: InputDecoration(
                  hintText: lp.translate('send_hint'),
                  border: InputBorder.none,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 8),
                ),
                onSubmitted: (value) => _sendMessage(value),
              ),
            ),
            IconButton(
              icon: Icon(_isRecording ? Icons.stop : Icons.mic_none_rounded,
                  color: _isRecording ? Colors.red : Colors.black54),
              onPressed: _toggleRecording,
            ),
            IconButton(
              icon: const Icon(Icons.send_rounded, color: Colors.blueAccent),
              onPressed: () => _sendMessage(_controller.text),
            ),
          ],
        ),
      ),
    );
  }
}



// REMOVED _CompletionDialog class as it's now external

/// ── Chat Bubble ────────────────────────────────────────────────────────────
class _ChatBubble extends StatelessWidget {
  final String? text;
  final String? imagePath;
  final bool isUser;
  final String? pdfUrl;
  final int? documentId;
  final List<String>? missingFields;
  final DateTime? time;
  final String actType;

  final LanguageProvider lp;

  const _ChatBubble({
    this.text,
    this.imagePath,
    required this.isUser,
    this.pdfUrl,
    this.documentId,
    this.missingFields,
    this.time,
    required this.actType,
    required this.lp,
  });

  void _showFullImage(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => Dialog.fullscreen(
        backgroundColor: Colors.black,
        child: Stack(
          children: [
            Center(
              child: InteractiveViewer(
                minScale: 0.5,
                maxScale: 4.0,
                child: imagePath != null
                    ? (kIsWeb
                        ? Image.network(imagePath!, fit: BoxFit.contain)
                        : Image.file(dart_io.File(imagePath!), fit: BoxFit.contain))
                    : const SizedBox.shrink(),
              ),
            ),
            Positioned(
              top: 40,
              right: 20,
              child: IconButton(
                icon: const Icon(Icons.close, color: Colors.white, size: 30),
                onPressed: () => Navigator.pop(context),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final timeStr =
        time != null ? DateFormat('HH:mm').format(time!) : "";

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!isUser) ...[
            const CircleAvatar(
              radius: 15,
              backgroundColor: kPrimaryColor,
              child:
                  Icon(Icons.auto_awesome, size: 12, color: Colors.white),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: isUser ? kUserBubble : kAiBubble,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(18),
                  topRight: const Radius.circular(18),
                  bottomLeft: Radius.circular(isUser ? 18 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 18),
                ),
                boxShadow: [
                  BoxShadow(
                      color: Colors.black.withOpacity(0.04),
                      blurRadius: 6,
                      offset: const Offset(0, 2))
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (imagePath != null)
                    GestureDetector(
                      onTap: () => _showFullImage(context),
                      child: Hero(
                        tag: imagePath!,
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(10),
                          child: kIsWeb
                              ? Image.network(imagePath!,
                                  height: 140,
                                  width: double.infinity,
                                  fit: BoxFit.cover)
                              : Image.file(dart_io.File(imagePath!),
                                  height: 140,
                                  width: double.infinity,
                                  fit: BoxFit.cover),
                        ),
                      ),
                    ),
                  if (text != null && text!.isNotEmpty) ...[
                    if (imagePath != null) const SizedBox(height: 8),
                    SelectableText(
                      text!,
                      style: const TextStyle(
                          fontSize: 14, color: Colors.black87, height: 1.4),
                    ),
                  ],
                  if (pdfUrl != null) ...[
                    const SizedBox(height: 12),
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        ElevatedButton.icon(
                          onPressed: () {
                            Navigator.push(
                                context,
                                MaterialPageRoute(
                                    builder: (_) => PdfViewerScreen(
                                        pdfUrl: pdfUrl!,
                                        title: actType == "mariage"
                                            ? "Acte de Mariage" 
                                            : "Acte de Vente",
                                        documentId: documentId,
                                        missingFields: missingFields,
                                        actType: actType,
                                    )));
                          },
                          icon: const Icon(Icons.picture_as_pdf, size: 16),
                          label: Text(lp.translate('see_pdf'),
                              style: const TextStyle(fontSize: 12)),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: kPrimaryColor,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(
                                horizontal: 14, vertical: 8),
                            shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10)),
                          ),
                        ),
                      ],
                    ),
                  ],
                  const SizedBox(height: 4),
                  Align(
                    alignment: Alignment.bottomRight,
                    child: Text(timeStr,
                        style: const TextStyle(
                            fontSize: 9, color: Colors.grey)),
                  ),
                ],
              ),
            ),
          ),
          if (isUser) ...[
            const SizedBox(width: 8),
            CircleAvatar(
              radius: 15,
              backgroundColor: Colors.blueGrey.shade100,
              child:
                  const Icon(Icons.person, size: 14, color: kPrimaryColor),
            ),
          ],
        ],
      ),
    );
  }
}

/// ── Typing dots animation ──────────────────────────────────────────────────
class _TypingDot extends StatefulWidget {
  final int delay;
  const _TypingDot({required this.delay});

  @override
  State<_TypingDot> createState() => _TypingDotState();
}

class _TypingDotState extends State<_TypingDot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 600));
    _anim = Tween(begin: 0.3, end: 1.0).animate(
        CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
    Future.delayed(Duration(milliseconds: widget.delay),
        () => _ctrl.repeat(reverse: true));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _anim,
      child: const CircleAvatar(
          radius: 4, backgroundColor: Colors.blueGrey),
    );
  }
}

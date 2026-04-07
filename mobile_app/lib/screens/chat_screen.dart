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

/// ── Constantes de design ───────────────────────────────────────────────────
const kNavy = Color(0xFF0D1B4B);
const kGold = Color(0xFFB8860B);
const kBgGrey = Color(0xFFF4F6FA);
const kWhite = Colors.white;
const kUserBubble = Color(0xFFE8EAF6);
const kAiBubble = Colors.white;

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

  XFile? _vendeurFile;
  XFile? _acheteurFile;

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

  Future<void> _startNewSession() async {
    try {
      final session = await ApiService.createChatSession();
      setState(() {
        _currentSessionId = session['id'];
        _messages.clear();
      });
      _loadSessions();
    } catch (e) {
      if (kDebugMode) print("Error creating session: $e");
    }
  }

  /// Envoie une réponse vers Gemini et affiche la réponse IA réelle.
  Future<void> _sendMessage(String text) async {
    if (text.isEmpty || _currentSessionId == null) return;

    final time = DateTime.now();
    setState(() {
      _messages.add({"text": text, "isUser": true, "time": time});
      _isSending = true;
    });
    _controller.clear();
    _scrollToBottom();

    try {
      final result = await ApiService.sendAiMessage(_currentSessionId!, text);
      final aiText = result['reply'] as String? ?? "Je traite votre demande…";

      setState(() {
        _messages.add({"text": aiText, "isUser": false, "time": DateTime.now()});
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
    final XFile? image = await _picker.pickImage(source: source);
    if (image == null) return;

    setState(() {
      if (_vendeurFile == null) {
        _vendeurFile = image;
        _messages.add({
          "text": "📷 Carte d'identité Vendeur envoyée.",
          "isUser": true,
          "image": image.path,
          "time": DateTime.now()
        });
        _messages.add({
          "text":
              "Carte d'identité du Vendeur reçue ✓\n\nMaintenant, veuillez envoyer la carte d'identité de **l'Acheteur**.",
          "isUser": false,
          "time": DateTime.now()
        });
      } else if (_acheteurFile == null) {
        _acheteurFile = image;
        _messages.add({
          "text": "📷 Carte d'identité Acheteur envoyée.",
          "isUser": true,
          "image": image.path,
          "time": DateTime.now()
        });
        _messages.add({
          "text": "⚙️ Analyse des pièces d'identité en cours… Génération de l'acte selon votre modèle officiel.",
          "isUser": false,
          "time": DateTime.now()
        });
        _scrollToBottom();
        _processIdCards();
      }
    });
    _scrollToBottom();
  }

  Future<void> _processIdCards() async {
    setState(() => _isSending = true);
    try {
      final res = await ApiService.sendIdCards(_vendeurFile!, _acheteurFile!);
      final vendeurNom = res['vendeur_extrait']?['nom'] ?? '—';
      final acheteurNom = res['acheteur_extrait']?['nom'] ?? '—';
      final docId = res['document_id'] as int?;
      final pdfUrl = ApiService.getFullUrl(res['pdf_url'] ?? '');
      final missingFields = List<String>.from(res['missing_fields'] ?? []);

      setState(() {
        _messages.add({
          "text":
              "✅ Brouillon généré !\n\n• **Vendeur** : $vendeurNom\n• **Acheteur** : $acheteurNom",
          "isUser": false,
          "pdfUrl": pdfUrl,
          "documentId": docId,
          "time": DateTime.now()
        });
        _vendeurFile = null;
        _acheteurFile = null;
      });
      _scrollToBottom();

      // Si des champs sont manquants, ouvrir le formulaire de complétion
      if (missingFields.isNotEmpty && docId != null) {
        await Future.delayed(const Duration(milliseconds: 700));
        if (mounted) {
          await _showCompletionDialog(docId, missingFields, pdfUrl);
        }
      }

      if (_currentSessionId != null) {
        await ApiService.addChatMessage(
            _currentSessionId!,
            "assistant",
            "Brouillon généré — Vendeur: $vendeurNom, Acheteur: $acheteurNom",
            "pdf");
      }
    } catch (e) {
      setState(() {
        _messages.add({
          "text": "❌ Erreur lors de la génération : $e",
          "isUser": false,
          "time": DateTime.now()
        });
        _vendeurFile = null;
        _acheteurFile = null;
      });
    } finally {
      setState(() => _isSending = false);
    }
  }

  /// Dialogue interactif pour compléter les champs manquants de l'acte.
  Future<void> _showCompletionDialog(
      int docId, List<String> missingFields, String oldPdfUrl) async {
    final Map<String, TextEditingController> controllers = {};
    final Map<String, String> fieldKeys = {
      "Prix de vente / Montant (MRU)": "prix",
      "Quartier de situation du bien": "quartier",
      "Moughataa (Département)": "moughataa",
      "Numéro de parcelle / Terrain": "parcelle",
      "Surface du terrain (m²)": "surface",
    };

    for (final field in missingFields) {
      if (fieldKeys.containsKey(field)) {
        controllers[field] = TextEditingController();
      }
    }

    if (controllers.isEmpty) return;

    setState(() {
      _messages.add({
        "text":
            "⚠️ L'acte est incomplet. ${controllers.length} information(s) manquante(s).\n\nUn formulaire va s'ouvrir pour les compléter.",
        "isUser": false,
        "time": DateTime.now()
      });
    });

    final result = await showDialog<Map<String, String>>(
      context: context,
      barrierDismissible: false,
      builder: (context) => _CompletionDialog(
        controllers: controllers,
        fieldKeys: fieldKeys,
        missingFields: missingFields,
      ),
    );

    if (result != null && result.isNotEmpty) {
      setState(() {
        _messages.add({
          "text": "📋 Informations complémentaires envoyées. Régénération en cours…",
          "isUser": true,
          "time": DateTime.now()
        });
        _isSending = true;
      });
      _scrollToBottom();

      try {
        final completed = await ApiService.completeAct(docId, result);
        final newStatus = completed['status'] ?? 'brouillon';
        final newPdfUrl = ApiService.getFullUrl(completed['pdf_url'] ?? '');
        final remaining =
            List<String>.from(completed['missing_fields'] ?? []);

        setState(() {
          _messages.add({
            "text": newStatus == 'valide'
                ? "✅ **Acte finalisé et validé !**\n\nLe PDF officiel est prêt."
                : "📄 Acte mis à jour. ${remaining.length} champ(s) encore manquant(s).",
            "isUser": false,
            "pdfUrl": newPdfUrl,
            "documentId": docId,
            "time": DateTime.now()
          });
        });
        _scrollToBottom();
      } catch (e) {
        setState(() {
          _messages.add({
            "text": "❌ Erreur lors de la finalisation : $e",
            "isUser": false,
            "time": DateTime.now()
          });
        });
      } finally {
        setState(() => _isSending = false);
      }
    } else {
      setState(() {
        _messages.add({
          "text":
              "Formulaire annulé. Vous pouvez télécharger le brouillon ou compléter plus tard.",
          "isUser": false,
          "pdfUrl": oldPdfUrl,
          "documentId": docId,
          "time": DateTime.now()
        });
      });
    }
  }

  void _handleLogout() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text("Déconnexion"),
        content: const Text("Voulez-vous vraiment vous déconnecter Maître ?"),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Annuler")),
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
            child: const Text("Déconnexion"),
          ),
        ],
      ),
    );
  }

  void _showAttachmentMenu() {
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
                title: const Text('Appareil photo'),
                subtitle: const Text('Carte d\'identité en direct'),
                onTap: () {
                  Navigator.pop(context);
                  _pickImage(ImageSource.camera);
                },
              ),
              ListTile(
                leading: const Icon(Icons.photo_library, color: kNavy),
                title: const Text('Galerie photo'),
                subtitle: const Text('Sélectionner depuis l\'album'),
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

  @override
  Widget build(BuildContext context) {
    final notaryName = ApiService.notaryName ?? "Maître";

    return Scaffold(
      backgroundColor: kBgGrey,
      drawer: _buildDrawer(),
      appBar: _buildAppBar(),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? _buildWelcomeScreen(notaryName)
                : _buildMessageList(),
          ),
          if (_isSending) _buildTypingIndicator(),
          _buildInputBar(),
        ],
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      elevation: 0,
      backgroundColor: kNavy,
      foregroundColor: kWhite,
      title: Row(
        children: [
          const Icon(Icons.auto_awesome, color: kGold, size: 20),
          const SizedBox(width: 8),
          const Text("Agentic Notary",
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(width: 8),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: Colors.green.withOpacity(0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text("Gemini 2.0",
                style: TextStyle(fontSize: 10, color: Colors.greenAccent)),
          ),
        ],
      ),
      actions: [
        Padding(
          padding: const EdgeInsets.only(right: 16.0),
          child: PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'logout') _handleLogout();
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                  value: 'profile',
                  child: ListTile(
                      leading: Icon(Icons.person),
                      title: Text("Mon Profil"),
                      dense: true)),
              const PopupMenuItem(
                  value: 'logout',
                  child: ListTile(
                      leading: Icon(Icons.logout, color: Colors.red),
                      title: Text("Déconnexion",
                          style: TextStyle(color: Colors.red)),
                      dense: true)),
            ],
            child: CircleAvatar(
              backgroundColor: Colors.white.withOpacity(0.15),
              child: const Icon(Icons.person, color: kWhite, size: 20),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildDrawer() {
    return Drawer(
      child: Column(
        children: [
          UserAccountsDrawerHeader(
            decoration: const BoxDecoration(color: kNavy),
            accountName: Text(ApiService.notaryName ?? "Notaire",
                style: const TextStyle(fontWeight: FontWeight.bold)),
            accountEmail: const Text("Professionnel du droit",
                style: TextStyle(fontSize: 12)),
            currentAccountPicture: const CircleAvatar(
                backgroundColor: kWhite,
                child: Icon(Icons.gavel, color: kNavy, size: 30)),
          ),
          ListTile(
            leading: const Icon(Icons.add_comment_outlined, color: kNavy),
            title: const Text("Nouvelle Discussion"),
            onTap: () {
              Navigator.pop(context);
              _startNewSession();
            },
          ),
          ListTile(
            leading:
                const Icon(Icons.folder_outlined, color: kNavy),
            title: const Text("Mes Actes"),
            onTap: () {
              Navigator.pop(context);
              Navigator.pushNamed(context, '/documents');
            },
          ),
          const Divider(),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(children: [
              Icon(Icons.history, size: 14, color: Colors.grey),
              SizedBox(width: 6),
              Text("HISTORIQUE RÉCENT",
                  style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: Colors.grey,
                      letterSpacing: 0.5)),
            ]),
          ),
          Expanded(
            child: _isLoadingSessions
                ? const Center(child: CircularProgressIndicator())
                : ListView.builder(
                    itemCount: _sessions.length,
                    itemBuilder: (context, index) {
                      final s = _sessions[index];
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
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildWelcomeScreen(String name) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 20),
            Text("Bonjour $name,",
                style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w300,
                    color: Colors.blueGrey)),
            const Text("Par où commencer ?",
                style: TextStyle(
                    fontSize: 30,
                    fontWeight: FontWeight.bold,
                    color: kNavy)),
            const SizedBox(height: 40),
            _buildActionCard(
              Icons.camera_alt_outlined,
              "Générer un acte de vente",
              "Scannez les CIN du Vendeur et de l'Acheteur.",
              onTap: () => _pickImage(ImageSource.camera),
              badgeText: "IA",
            ),
            _buildActionCard(
              Icons.description_outlined,
              "Consulter mes documents",
              "Accédez aux actes déjà générés et validés.",
              onTap: () => Navigator.pushNamed(context, '/documents'),
            ),
            _buildActionCard(
              Icons.gavel_outlined,
              "Conseil juridique",
              "Posez une question à l'IA notariale.",
              onTap: () =>
                  _sendMessage("Bonjour Maître, comment puis-je vous aider ?"),
              badgeText: "Gemini",
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionCard(IconData icon, String title, String subtitle,
      {VoidCallback? onTap, String? badgeText}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        margin: const EdgeInsets.only(bottom: 14),
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: kWhite,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
                color: Colors.black.withOpacity(0.06),
                blurRadius: 12,
                offset: const Offset(0, 4))
          ],
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                  color: kNavy.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(12)),
              child: Icon(icon, color: kNavy, size: 26),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(title,
                          style: const TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 15)),
                      if (badgeText != null) ...[
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                              color: kGold.withOpacity(0.15),
                              borderRadius: BorderRadius.circular(8)),
                          child: Text(badgeText,
                              style: const TextStyle(
                                  fontSize: 9,
                                  color: kGold,
                                  fontWeight: FontWeight.bold)),
                        ),
                      ]
                    ],
                  ),
                  const SizedBox(height: 3),
                  Text(subtitle,
                      style:
                          const TextStyle(color: Colors.grey, fontSize: 12)),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: Colors.grey),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageList() {
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
          time: msg["time"],
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

  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: kWhite,
        boxShadow: [
          BoxShadow(
              color: Colors.black.withOpacity(0.06),
              blurRadius: 10,
              offset: const Offset(0, -3))
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            IconButton(
              icon: const Icon(Icons.attach_file, color: Colors.blueGrey),
              onPressed: _showAttachmentMenu,
              tooltip: "Joindre une pièce d'identité",
            ),
            Expanded(
              child: TextField(
                controller: _controller,
                maxLines: null,
                textInputAction: TextInputAction.send,
                onSubmitted: _sendMessage,
                decoration: InputDecoration(
                  hintText: "Demandez à votre assistant notarial…",
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(30),
                    borderSide: BorderSide.none,
                  ),
                  filled: true,
                  fillColor: kBgGrey,
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: 20, vertical: 10),
                ),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              icon: Icon(
                  _isRecording ? Icons.stop_circle : Icons.mic_none_outlined,
                  color: _isRecording ? Colors.red : Colors.blueGrey),
              onPressed: _toggleRecording,
              tooltip: _isRecording
                  ? "Arrêter l'enregistrement"
                  : "Message vocal",
            ),
            const SizedBox(width: 4),
            CircleAvatar(
              radius: 22,
              backgroundColor: kNavy,
              child: IconButton(
                icon: const Icon(Icons.send, size: 18, color: Colors.white),
                onPressed: () => _sendMessage(_controller.text),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// ── Dialogue de complétion des champs manquants ────────────────────────────
class _CompletionDialog extends StatelessWidget {
  final Map<String, TextEditingController> controllers;
  final Map<String, String> fieldKeys;
  final List<String> missingFields;

  const _CompletionDialog({
    required this.controllers,
    required this.fieldKeys,
    required this.missingFields,
  });

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      title: const Row(
        children: [
          Icon(Icons.edit_document, color: kNavy),
          SizedBox(width: 10),
          Expanded(
            child: Text("Compléter l'acte de vente",
                style:
                    TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
      content: SizedBox(
        width: double.maxFinite,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(10),
                  border:
                      Border.all(color: Colors.amber.shade200),
                ),
                child: Text(
                  "⚠️ ${controllers.length} information(s) manquante(s). "
                  "Remplissez les champs ci-dessous pour finaliser l'acte.",
                  style: const TextStyle(fontSize: 12),
                ),
              ),
              const SizedBox(height: 16),
              ...controllers.entries.map((entry) {
                final fieldName = entry.key;
                final controller = entry.value;
                final hint = _getHint(fieldName);
                return Padding(
                  padding: const EdgeInsets.only(bottom: 14),
                  child: TextField(
                    controller: controller,
                    decoration: InputDecoration(
                      labelText: fieldName,
                      hintText: hint,
                      prefixIcon: Icon(_getIcon(fieldName),
                          color: kNavy, size: 20),
                      border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12)),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide:
                            const BorderSide(color: kNavy, width: 2),
                      ),
                    ),
                  ),
                );
              }),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, null),
          child: const Text("Plus tard",
              style: TextStyle(color: Colors.grey)),
        ),
        ElevatedButton.icon(
          onPressed: () {
            final result = <String, String>{};
            for (final entry in controllers.entries) {
              final key = fieldKeys[entry.key];
              final val = entry.value.text.trim();
              if (key != null && val.isNotEmpty) {
                result[key] = val;
              }
            }
            Navigator.pop(context, result);
          },
          icon: const Icon(Icons.check, size: 16),
          label: const Text("Finaliser l'acte"),
          style: ElevatedButton.styleFrom(
            backgroundColor: kNavy,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12)),
          ),
        ),
      ],
    );
  }

  String _getHint(String field) {
    if (field.contains("Prix")) return "ex: 5000000";
    if (field.contains("Quartier")) return "ex: Tevragh Zeina";
    if (field.contains("Moughataa")) return "ex: Tevragh Zeina";
    if (field.contains("parcelle")) return "ex: 123/B";
    if (field.contains("Surface")) return "ex: 250";
    return "";
  }

  IconData _getIcon(String field) {
    if (field.contains("Prix")) return Icons.payments_outlined;
    if (field.contains("Quartier")) return Icons.location_city_outlined;
    if (field.contains("Moughataa")) return Icons.map_outlined;
    if (field.contains("parcelle")) return Icons.grid_view_outlined;
    if (field.contains("Surface")) return Icons.straighten_outlined;
    return Icons.edit_outlined;
  }
}

/// ── Chat Bubble ────────────────────────────────────────────────────────────
class _ChatBubble extends StatelessWidget {
  final String? text;
  final String? imagePath;
  final bool isUser;
  final String? pdfUrl;
  final int? documentId;
  final DateTime? time;

  const _ChatBubble({
    this.text,
    this.imagePath,
    required this.isUser,
    this.pdfUrl,
    this.documentId,
    this.time,
  });

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
              backgroundColor: kNavy,
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
                    ClipRRect(
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
                  if (text != null && text!.isNotEmpty) ...[
                    if (imagePath != null) const SizedBox(height: 8),
                    Text(text!,
                        style: const TextStyle(
                            fontSize: 14, color: Colors.black87, height: 1.4)),
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
                                        title: "Acte de Vente")));
                          },
                          icon: const Icon(Icons.picture_as_pdf, size: 16),
                          label: const Text("Voir PDF",
                              style: TextStyle(fontSize: 12)),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: kNavy,
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
                  const Icon(Icons.person, size: 14, color: kNavy),
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

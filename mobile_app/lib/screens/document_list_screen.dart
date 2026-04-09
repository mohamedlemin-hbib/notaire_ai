import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'pdf_viewer_screen.dart';
import 'package:file_picker/file_picker.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter/foundation.dart';

class DocumentListScreen extends StatefulWidget {
  const DocumentListScreen({super.key});

  @override
  State<DocumentListScreen> createState() => _DocumentListScreenState();
}

class _DocumentListScreenState extends State<DocumentListScreen> {
  List<dynamic> _documents = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadDocuments();
  }

  Future<void> _loadDocuments() async {
    try {
      final docs = await ApiService.getDocuments();
      setState(() {
        _documents = docs;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Erreur lors du chargement : $e")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Mes Actes", style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF1A237E),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.add_circle_outline),
            tooltip: "Ajouter un Modèle d'Acte",
            onPressed: () => _showUploadDialog(),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadDocuments,
          ),
        ],
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator())
        : ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: _documents.length,
            itemBuilder: (context, index) {
              final doc = _documents[index];
              return Card(
                elevation: 2,
                margin: const EdgeInsets.only(bottom: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: ListTile(
                  leading: const Icon(Icons.description, color: Color(0xFF1A237E), size: 32),
                  title: Text(doc['title'] ?? "Acte sans titre", style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text("Créé le : ${doc['created_at']?.split('T')[0] ?? 'Inconnu'}"),
                  trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                  onTap: () {
                    final pdfUrl = doc['pdf_url'];
                    if (pdfUrl != null) {
                      final fullUrl = ApiService.getFullUrl(pdfUrl);
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => PdfViewerScreen(
                            pdfUrl: fullUrl,
                            title: doc['title'] ?? "Acte",
                          ),
                        ),
                      );
                    }
                  },
                ),
              );
            },
          ),
    );
  }

  void _showUploadDialog() {
    String actType = "Vente Immobilière";
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Ajouter un Modèle d'Acte"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text("Choisissez un fichier .pdf ou .docx pour servir de modèle à l'IA."),
            const SizedBox(height: 16),
            TextField(
              decoration: const InputDecoration(labelText: "Type d'acte", hintText: "Ex: Vente, Mariage, etc."),
              onChanged: (val) => actType = val,
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("Annuler")),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              FilePickerResult? result = await FilePicker.platform.pickFiles(
                type: FileType.custom,
                allowedExtensions: ['pdf', 'docx'],
              );

              if (result != null) {
                setState(() => _isLoading = true);
                try {
                  final platformFile = result.files.single;
                  XFile xFile;
                  if (kIsWeb) {
                    xFile = XFile.fromData(platformFile.bytes!, name: platformFile.name);
                  } else {
                    xFile = XFile(platformFile.path!);
                  }
                  
                  await ApiService.uploadTemplate(xFile, actType);
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text("Modèle ajouté avec succès !")),
                    );
                  }
                } catch (e) {
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text("Erreur lors de l'upload : $e")),
                    );
                  }
                } finally {
                  setState(() => _isLoading = false);
                  _loadDocuments();
                }
              }
            },
            child: const Text("Choisir un fichier"),
          ),
        ],
      ),
    );
  }
}

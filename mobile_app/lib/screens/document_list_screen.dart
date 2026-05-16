import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/language_provider.dart';
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
    final lp = Provider.of<LanguageProvider>(context, listen: false);
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
          SnackBar(content: Text("${lp.translate('error_loading')} : $e")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final lp = Provider.of<LanguageProvider>(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(lp.translate('my_acts'), style: const TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF1A237E),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.add_circle_outline),
            tooltip: lp.translate('add_template'),
            onPressed: () => _showUploadDialog(lp),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: lp.translate('refresh'),
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
                  title: Text(doc['title'] ?? lp.translate('no_title'), style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text("${lp.translate('created_on')} : ${doc['created_at']?.split('T')[0] ?? '...'}"),
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
                            documentId: doc['id'],
                            missingFields: doc['missing_fields'] != null ? List<String>.from(doc['missing_fields']) : null,
                            actType: doc['act_type'],
                            status: doc['status'],
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

  void _showUploadDialog(LanguageProvider lp) {
    String actType = lp.translate('immobilier');
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(lp.translate('add_template')),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(lp.translate('add_template_desc')),
            const SizedBox(height: 16),
            TextField(
              decoration: InputDecoration(
                labelText: lp.isArabic ? "نوع العقد" : "Type d'acte", 
                hintText: "Ex: Vente, Mariage, etc."
              ),
              onChanged: (val) => actType = val,
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text(lp.translate('cancel'))),
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
                      SnackBar(content: Text(lp.translate('upload_success'))),
                    );
                  }
                } catch (e) {
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text("${lp.translate('error_upload')} : $e")),
                    );
                  }
                } finally {
                  setState(() => _isLoading = false);
                  _loadDocuments();
                }
              }
            },
            child: Text(lp.translate('choose_file')),
          ),
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:syncfusion_flutter_pdfviewer/pdfviewer.dart';
import 'package:http/http.dart' as http;
import 'dart:typed_data';
import 'package:mobile_app/widgets/completion_dialog.dart';
import 'package:mobile_app/services/api_service.dart';
import 'package:provider/provider.dart';
import 'package:mobile_app/providers/language_provider.dart';

class PdfViewerScreen extends StatefulWidget {
  final String pdfUrl;
  final String title;
  final int? documentId;
  final List<String>? missingFields;
  final String? actType;
  final String? status;

  const PdfViewerScreen({
    super.key,
    required this.pdfUrl,
    required this.title,
    this.documentId,
    this.missingFields,
    this.actType,
    this.status,
  });

  @override
  State<PdfViewerScreen> createState() => _PdfViewerScreenState();
}

class _PdfViewerScreenState extends State<PdfViewerScreen> {
  Uint8List? _pdfBytes;
  bool _isLoading = true;
  String? _errorMessage;
  final PdfViewerController _pdfController = PdfViewerController();
  List<String>? _currentMissingFields;
  String? _currentStatus;

  @override
  void initState() {
    super.initState();
    _currentMissingFields = widget.missingFields;
    _currentStatus = widget.status;
    _fetchPdf();
  }

  Future<void> _fetchPdf() async {
    try {
      String cleanUrl = widget.pdfUrl;

      // Correction du double URL
      if (cleanUrl.contains("http://localhost:8000http")) {
        cleanUrl = cleanUrl.replaceFirst("http://localhost:8000", "");
      }

      if (kDebugMode) print("DEBUG PDF VIEWER: Fetching '$cleanUrl'");

      final response = await http.get(
        Uri.parse(cleanUrl),
        headers: ApiService.token != null ? {'Authorization': 'Bearer ${ApiService.token}'} : {},
      ).timeout(
        const Duration(seconds: 30),
        onTimeout: () {
          final lp = Provider.of<LanguageProvider>(context, listen: false);
          throw Exception(lp.translate('timeout'));
        },
      );

      if (response.statusCode == 200) {
        setState(() {
          _pdfBytes = response.bodyBytes;
          _isLoading = false;
        });
      } else {
        final lp = Provider.of<LanguageProvider>(context, listen: false);
        setState(() {
          _errorMessage =
              "${lp.translate('fail')} ${response.statusCode} : ${lp.translate('pdf_error_fetch')}.";
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Erreur : $e";
        _isLoading = false;
      });
    }
  }

  Future<void> _handleCompletion() async {
    if (widget.documentId == null || _currentMissingFields == null || _currentMissingFields!.isEmpty) return;

    final lp = Provider.of<LanguageProvider>(context, listen: false);
    final fieldKeys = CompletionDialog.getFieldKeys();
    final Map<String, TextEditingController> controllers = {};
    for (final field in _currentMissingFields!) {
      if (fieldKeys.containsKey(field)) {
        controllers[field] = TextEditingController();
      }
    }

    if (controllers.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(lp.isArabic ? "لم يتم العثور على حقول متوافقة للإكمال." : "Aucun champ compatible trouvé pour la complétion.")),
      );
      return;
    }

    final result = await showDialog<Map<String, String>>(
      context: context,
      barrierDismissible: false,
      builder: (context) => CompletionDialog(
        controllers: controllers,
        fieldKeys: fieldKeys,
        missingFields: _currentMissingFields!,
        actType: widget.actType,
      ),
    );

    if (result != null && result.isNotEmpty) {
      setState(() {
        _isLoading = true;
        _errorMessage = null;
      });

      try {
        final lang = Provider.of<LanguageProvider>(context, listen: false).currentLocale.languageCode;
        final completed = await ApiService.completeAct(widget.documentId!, result, lang);
        final remaining = List<String>.from(completed['missing_fields'] ?? []);
        
        setState(() {
          _currentMissingFields = remaining;
          _pdfBytes = null; // Forces re-fetch
        });
        
        await _fetchPdf();
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(remaining.isEmpty 
                ? lp.translate('complete_success') 
                : "${lp.translate('complete_update')} ${remaining.length} ${lp.translate('fields_left')}"),
              backgroundColor: remaining.isEmpty ? Colors.green : Colors.orange,
            ),
          );
        }
      } catch (e) {
        setState(() {
          _errorMessage = "${lp.isArabic ? "خطأ أثناء الإكمال" : "Erreur lors de la complétion"} : $e";
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _handleSeal() async {
    if (widget.documentId == null) return;

    final lp = Provider.of<LanguageProvider>(context, listen: false);
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(lp.translate('seal_q')),
        content: Text(
          lp.translate('seal_desc'),
          style: const TextStyle(fontSize: 14),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(lp.translate('cancel'))),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF0D1B4B), foregroundColor: Colors.white),
            child: Text(lp.translate('seal_button')),
          ),
        ],
      ),
    );

    if (confirm == true) {
      setState(() {
        _isLoading = true;
      });

      try {
        await ApiService.sealAct(widget.documentId!);
        setState(() {
          _currentStatus = 'scelle';
          _isLoading = false;
        });

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(lp.translate('seal_success')),
              backgroundColor: Colors.indigo,
            ),
          );
        }
      } catch (e) {
        setState(() {
          _errorMessage = "Erreur lors du scellement : $e";
          _isLoading = false;
        });
      }
    }
  }

  void _openInBrowser() {

    // Compatible web et mobile
    if (kIsWeb) {
      // ignore: avoid_web_libraries_in_flutter
      // Utilise la navigation URL directe sur le web
      _launchUrl(widget.pdfUrl);
    } else {
      _launchUrl(widget.pdfUrl);
    }
  }

  void _launchUrl(String url) {
    final lp = Provider.of<LanguageProvider>(context, listen: false);
    // On web, on utilise url_launcher si disponible
    // Pour l'instant on affiche l'URL
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(lp.translate('open_link')),
        content: SelectableText(url),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: Text(lp.isArabic ? "إغلاق" : "Fermer"))
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final lp = Provider.of<LanguageProvider>(context);
    bool hasMissing = (_currentMissingFields != null && _currentMissingFields!.isNotEmpty);

    return Scaffold(
      backgroundColor: const Color(0xFFF4F6FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0D1B4B),
        foregroundColor: Colors.white,
        title: Row(
          children: [
            const Icon(Icons.picture_as_pdf, color: Color(0xFFB8860B), size: 20),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                widget.title,
                style: const TextStyle(
                    fontWeight: FontWeight.bold, fontSize: 15),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
        actions: [
          if (!_isLoading && _currentStatus != 'scelle') ...[
            if (hasMissing)
              TextButton.icon(
                onPressed: _handleCompletion,
                icon: const Icon(Icons.edit_note, color: Colors.amber),
                label: Text(lp.translate('complete'), style: const TextStyle(color: Colors.white, fontSize: 13)),
              ),
            TextButton.icon(
              onPressed: _handleSeal,
              icon: const Icon(Icons.verified, color: Colors.lightBlueAccent),
              label: Text(lp.isArabic ? "ختم" : "Sceller", style: const TextStyle(color: Colors.white, fontSize: 13)),
            ),
          ],
          if (_currentStatus == 'scelle')
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8.0),
              child: Chip(
                label: Text(lp.translate('sealed'), style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                backgroundColor: Colors.green,
                padding: EdgeInsets.zero,
                visualDensity: VisualDensity.compact,
              ),
            ),
          if (!_isLoading && _pdfBytes != null) ...[
            IconButton(
              icon: const Icon(Icons.zoom_in),
              tooltip: lp.translate('zoom_in'),
              onPressed: () => _pdfController.zoomLevel =
                  (_pdfController.zoomLevel + 0.25).clamp(0.5, 3.0),
            ),
            IconButton(
              icon: const Icon(Icons.zoom_out),
              tooltip: lp.translate('zoom_out'),
              onPressed: () => _pdfController.zoomLevel =
                  (_pdfController.zoomLevel - 0.25).clamp(0.5, 3.0),
            ),
          ],
          IconButton(
            icon: const Icon(Icons.open_in_new),
            tooltip: lp.translate('open_link'),
            onPressed: _openInBrowser,
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: lp.translate('refresh'),
            onPressed: () {
              setState(() {
                _isLoading = true;
                _errorMessage = null;
                _pdfBytes = null;
              });
              _fetchPdf();
            },
          ),
        ],
      ),
      body: _isLoading
          ? _buildLoadingState(lp)
          : _errorMessage != null
              ? _buildErrorState(lp)
              : _buildPdfViewer(lp),
    );
  }

  Widget _buildLoadingState(LanguageProvider lp) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(
            color: Color(0xFF0D1B4B),
            strokeWidth: 3,
          ),
          const SizedBox(height: 20),
          Text(
            lp.translate('pdf_loading'),
            style: const TextStyle(color: Colors.blueGrey, fontSize: 14),
          ),
          const SizedBox(height: 8),
          Text(
            lp.translate('pdf_fetch'),
            style: TextStyle(color: Colors.grey.shade500, fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState(LanguageProvider lp) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.red.shade50,
                shape: BoxShape.circle,
              ),
              child: Icon(Icons.error_outline,
                  color: Colors.red.shade400, size: 48),
            ),
            const SizedBox(height: 20),
            Text(
              lp.translate('pdf_error_fetch'),
              style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                  color: Color(0xFF0D1B4B)),
            ),
            const SizedBox(height: 8),
            Text(
              _errorMessage ?? lp.translate('fail'),
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.grey, fontSize: 13),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () {
                setState(() {
                  _isLoading = true;
                  _errorMessage = null;
                  _pdfBytes = null;
                });
                _fetchPdf();
              },
              icon: const Icon(Icons.refresh, size: 16),
              label: Text(lp.translate('retry')),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF0D1B4B),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                padding: const EdgeInsets.symmetric(
                    horizontal: 24, vertical: 12),
              ),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _openInBrowser,
              icon: const Icon(Icons.open_in_new, size: 16),
              label: Text(lp.translate('open_link')),
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: Color(0xFF0D1B4B)),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                padding: const EdgeInsets.symmetric(
                    horizontal: 24, vertical: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPdfViewer(LanguageProvider lp) {
    return SfPdfViewer.memory(
      _pdfBytes!,
      controller: _pdfController,
      enableDoubleTapZooming: true,
      onDocumentLoadFailed: (PdfDocumentLoadFailedDetails details) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("${lp.isArabic ? "خطأ في العرض" : "Erreur d'affichage"} : ${details.error}"),
            backgroundColor: Colors.red,
          ),
        );
      },
    );
  }
}

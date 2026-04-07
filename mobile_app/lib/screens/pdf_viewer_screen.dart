import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:syncfusion_flutter_pdfviewer/pdfviewer.dart';
import 'package:http/http.dart' as http;
import 'dart:typed_data';

class PdfViewerScreen extends StatefulWidget {
  final String pdfUrl;
  final String title;

  const PdfViewerScreen(
      {super.key, required this.pdfUrl, required this.title});

  @override
  State<PdfViewerScreen> createState() => _PdfViewerScreenState();
}

class _PdfViewerScreenState extends State<PdfViewerScreen> {
  Uint8List? _pdfBytes;
  bool _isLoading = true;
  String? _errorMessage;
  final PdfViewerController _pdfController = PdfViewerController();

  @override
  void initState() {
    super.initState();
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

      final response = await http.get(Uri.parse(cleanUrl)).timeout(
        const Duration(seconds: 30),
        onTimeout: () => throw Exception("Délai d'attente dépassé"),
      );

      if (response.statusCode == 200) {
        setState(() {
          _pdfBytes = response.bodyBytes;
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage =
              "Erreur serveur ${response.statusCode} : Impossible de charger le PDF.";
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
    // On web, on utilise url_launcher si disponible
    // Pour l'instant on affiche l'URL
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Lien PDF"),
        content: SelectableText(url),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text("Fermer"))
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
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
          if (!_isLoading && _pdfBytes != null) ...[
            IconButton(
              icon: const Icon(Icons.zoom_in),
              tooltip: "Zoom avant",
              onPressed: () => _pdfController.zoomLevel =
                  (_pdfController.zoomLevel + 0.25).clamp(0.5, 3.0),
            ),
            IconButton(
              icon: const Icon(Icons.zoom_out),
              tooltip: "Zoom arrière",
              onPressed: () => _pdfController.zoomLevel =
                  (_pdfController.zoomLevel - 0.25).clamp(0.5, 3.0),
            ),
          ],
          IconButton(
            icon: const Icon(Icons.open_in_new),
            tooltip: "Ouvrir le lien",
            onPressed: _openInBrowser,
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: "Recharger",
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
          ? _buildLoadingState()
          : _errorMessage != null
              ? _buildErrorState()
              : _buildPdfViewer(),
    );
  }

  Widget _buildLoadingState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(
            color: Color(0xFF0D1B4B),
            strokeWidth: 3,
          ),
          const SizedBox(height: 20),
          const Text(
            "Chargement du PDF…",
            style: TextStyle(color: Colors.blueGrey, fontSize: 14),
          ),
          const SizedBox(height: 8),
          Text(
            "Document en cours de récupération",
            style: TextStyle(color: Colors.grey.shade500, fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState() {
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
            const Text(
              "Impossible de charger le PDF",
              style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                  color: Color(0xFF0D1B4B)),
            ),
            const SizedBox(height: 8),
            Text(
              _errorMessage ?? "Erreur inconnue",
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
              label: const Text("Réessayer"),
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
              label: const Text("Voir l'URL"),
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

  Widget _buildPdfViewer() {
    return SfPdfViewer.memory(
      _pdfBytes!,
      controller: _pdfController,
      enableDoubleTapZooming: true,
      onDocumentLoadFailed: (PdfDocumentLoadFailedDetails details) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Erreur d'affichage : ${details.error}"),
            backgroundColor: Colors.red,
          ),
        );
      },
    );
  }
}

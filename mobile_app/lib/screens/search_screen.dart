import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/language_provider.dart';
import 'pdf_viewer_screen.dart';
import 'package:intl/intl.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final TextEditingController _searchController = TextEditingController();
  List<dynamic> _results = [];
  bool _isLoading = false;
  String? _selectedActType;

  // Removed _actTypes as it's now dynamically translated in _buildSearchHeader

  Future<void> _performSearch() async {
    final lp = Provider.of<LanguageProvider>(context, listen: false);
    final query = _searchController.text.trim();
    
    // Règle 1 : Rien ne s'affiche si la barre est vide
    if (query.isEmpty) {
      setState(() {
        _results = [];
        _isLoading = false;
      });
      return;
    }

    // Règle 2 : Si c'est un NNI (numérique), il doit être complet (10 chiffres)
    final isNumeric = RegExp(r'^\d+$').hasMatch(query);
    if (isNumeric && query.length < 10) {
      setState(() {
        _results = [];
        _isLoading = false;
      });
      return;
    }

    // Règle 3 : Si c'est du texte, minimum 3 caractères pour éviter les résultats trop larges
    if (!isNumeric && query.length < 3) {
      setState(() {
        _results = [];
        _isLoading = false;
      });
      return;
    }

    setState(() => _isLoading = true);
    try {
      final results = await ApiService.searchDocuments(
        q: query,
        actType: _selectedActType,
      );
      setState(() {
        _results = results;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("${lp.translate('search_short')} : $e")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final lp = Provider.of<LanguageProvider>(context);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        title: Text(lp.translate('search_filter'), style: const TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF1A237E),
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: Column(
        children: [
          _buildSearchHeader(lp),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF1A237E)))
                : _results.isEmpty
                    ? _buildEmptyState(lp)
                    : _buildResultsList(lp),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchHeader(LanguageProvider lp) {
    final actTypes = [
      {'label': lp.translate('all_acts'), 'value': ''},
      {'label': lp.translate('immobilier'), 'value': 'vente_immobilier'},
      {'label': lp.translate('vehicule'), 'value': 'vente_vehicule'},
      {'label': lp.translate('societe'), 'value': 'vente_societe'},
      {'label': lp.translate('mariage'), 'value': 'mariage'},
      {'label': lp.translate('testament'), 'value': 'testament'},
      {'label': lp.translate('hypotheque'), 'value': 'hypotheque'},
    ];

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: Color(0xFF1A237E),
        borderRadius: BorderRadius.only(
          bottomLeft: Radius.circular(24),
          bottomRight: Radius.circular(24),
        ),
      ),
      child: Column(
        children: [
          TextField(
            controller: _searchController,
            onChanged: (_) => _performSearch(),
            onSubmitted: (_) => _performSearch(),
            textAlign: lp.isArabic ? TextAlign.right : TextAlign.left,
            style: const TextStyle(color: Colors.white),
            decoration: InputDecoration(
              hintText: lp.translate('search_query_hint'),
              hintStyle: TextStyle(color: Colors.white.withOpacity(0.6)),
              prefixIcon: const Icon(Icons.search, color: Colors.white),
              filled: true,
              fillColor: Colors.white.withOpacity(0.1),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(15),
                borderSide: BorderSide.none,
              ),
              contentPadding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
          const SizedBox(height: 12),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: actTypes.map((type) {
                final isSelected = _selectedActType == type['value'] || (_selectedActType == null && type['value'] == '');
                return Padding(
                  padding: const EdgeInsets.only(right: 8, left: 8),
                  child: FilterChip(
                    label: Text(type['label']!),
                    selected: isSelected,
                    onSelected: (selected) {
                      setState(() {
                        _selectedActType = type['value'] == '' ? null : type['value'];
                      });
                      _performSearch();
                    },
                    selectedColor: const Color(0xFFC5A059),
                    labelStyle: TextStyle(
                      color: isSelected ? Colors.white : Colors.white70,
                      fontSize: 12,
                    ),
                    backgroundColor: Colors.white.withOpacity(0.1),
                    checkmarkColor: Colors.white,
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(LanguageProvider lp) {
    final query = _searchController.text.trim();
    final isNumeric = RegExp(r'^\d+$').hasMatch(query);

    String mainMsg = lp.translate('search_start');
    String subMsg = lp.translate('search_start_desc');

    if (query.isNotEmpty) {
      if (isNumeric && query.length < 10) {
        mainMsg = lp.translate('nni_incomplete');
        subMsg = lp.translate('nni_incomplete_desc');
      } else if (!isNumeric && query.length < 3) {
        mainMsg = lp.translate('search_short');
        subMsg = lp.translate('search_short_desc');
      } else {
        mainMsg = lp.translate('no_result_found');
        subMsg = lp.translate('no_result_found_desc');
      }
    }

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            query.isEmpty || (isNumeric && query.length < 10) || (!isNumeric && query.length < 3)
                ? Icons.search_rounded
                : Icons.search_off_rounded,
            size: 80,
            color: Colors.grey.withOpacity(0.5),
          ),
          const SizedBox(height: 16),
          Text(
            mainMsg,
            style: const TextStyle(fontSize: 16, color: Colors.grey, fontWeight: FontWeight.w500),
          ),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Text(
              subMsg,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: Colors.grey.withOpacity(0.7)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResultsList(LanguageProvider lp) {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _results.length,
      itemBuilder: (context, index) {
        final doc = _results[index];
        final date = DateTime.parse(doc['created_at']);
        final dateStr = DateFormat('dd MMMM yyyy à HH:mm', lp.isArabic ? 'ar_MA' : 'fr_FR').format(date);
        
        return Card(
          elevation: 0,
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: BorderSide(color: Colors.grey.shade200),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            leading: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFF1A237E).withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.description_rounded, color: Color(0xFF1A237E)),
            ),
            title: Text(
              doc['title'] ?? lp.translate('no_title'),
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                Text(
                  _formatActType(doc['act_type'], lp),
                  style: const TextStyle(color: Color(0xFFC5A059), fontWeight: FontWeight.w600, fontSize: 12),
                ),
                const SizedBox(height: 2),
                Text(
                  dateStr,
                  style: TextStyle(color: Colors.grey.shade600, fontSize: 11),
                ),
              ],
            ),
            trailing: const Icon(Icons.chevron_right_rounded, color: Colors.grey),
            onTap: () {
              final pdfUrl = doc['pdf_url'];
              if (pdfUrl != null) {
                final fullUrl = ApiService.getFullUrl(pdfUrl);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => PdfViewerScreen(
                      pdfUrl: fullUrl,
                      title: doc['title'] ?? lp.translate('see_pdf'),
                      documentId: doc['id'],
                      actType: doc['act_type'],
                    ),
                  ),
                );
              }
            },
          ),
        );
      },
    );
  }

  String _formatActType(String? type, LanguageProvider lp) {
    switch (type) {
      case 'vente_immobilier': return lp.translate('immobilier');
      case 'vente_vehicule': return lp.translate('vehicule');
      case 'vente_societe': return lp.translate('societe');
      case 'mariage': return lp.translate('mariage');
      case 'testament': return lp.translate('testament');
      case 'hypotheque': return lp.translate('hypotheque');
      default: return lp.translate('notarial_act');
    }
  }
}

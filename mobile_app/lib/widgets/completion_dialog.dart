import 'package:flutter/material.dart';

const kPrimaryColor = Color(0xFF1A237E);

class CompletionDialog extends StatelessWidget {
  final Map<String, TextEditingController> controllers;
  final Map<String, String> fieldKeys;
  final List<String> missingFields;
  final String? actType;

  const CompletionDialog({
    super.key,
    required this.controllers,
    required this.fieldKeys,
    required this.missingFields,
    this.actType,
  });

  /// Retourne le mapping complet pour tous les types d'actes
  static Map<String, String> getFieldKeys() {
    return {
      // Vente Immobilier
      "Prix de vente / Montant (MRU)": "prix",
      "Quartier de situation du bien": "quartier",
      "Moughataa (Département)": "moughataa",
      "Numéro de parcelle / Terrain": "parcelle",
      "Surface du terrain (m²)": "surface",
      
      // Mariage
      "Nom du Wali (Tuteur légal)": "wali",
      "Premier Témoin": "temoin1",
      "Second Témoin": "temoin2",
      "Montant de la Dot (Mahr)": "mahr",
      "État de la Dot (Payé/Différé)": "mahr_etat",
      "Conditions particulières": "conditions",
      
      // Vente Véhicule
      "Marque et Modèle du véhicule": "marque_modele",
      "Numéro de Châssis": "chassis",
      "Numéro d'immatriculation": "matricule",
      "Prix de vente (MRU)": "prix",
      "Année de mise en circulation": "annee",

      // Vente Société / Cession de parts
      "Dénomination de la société": "nom_societe",
      "Registre du Commerce": "registre_commerce",
      "Nombre de parts cédées": "parts_cedees",
      "Valeur nominale": "valeur_nominale",
      "Prix de cession (MRU)": "prix",
      "Prix en lettres": "prix_lettres",
      
      // Commun
      "Prix de cession": "prix",
      "Prix": "prix",
      "Date d'effet": "date_effet",
    };
  }

  @override
  Widget build(BuildContext context) {
    String titleText = "Compléter l'acte";
    if (actType == "mariage") titleText = "Compléter l'acte de mariage";
    else if (actType == "vente_immobilier") titleText = "Compléter l'acte de vente immobilière";
    else if (actType == "vente_vehicule") titleText = "Compléter l'acte de vente de véhicule";
    else if (actType == "vente_societe") titleText = "Compléter l'acte de cession de parts";

    return AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      title: Row(
        children: [
          const Icon(Icons.edit_document, color: kPrimaryColor),
          const SizedBox(width: 10),
          Expanded(
            child: Text(titleText,
                style: const TextStyle(
                    fontSize: 16, fontWeight: FontWeight.bold)),
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
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.amber.shade200),
                ),
                child: Text(
                  "⚠️ ${controllers.length} information(s) manquante(s). "
                  "Remplissez ces champs pour générer l'acte final sans points vides.",
                  style: const TextStyle(fontSize: 12, color: Colors.brown),
                ),
              ),
              const SizedBox(height: 16),
              ...controllers.entries.map((entry) {
                final fieldName = entry.key;
                final controller = entry.value;
                return Padding(
                  padding: const EdgeInsets.only(bottom: 14),
                  child: TextField(
                    controller: controller,
                    decoration: InputDecoration(
                      labelText: fieldName,
                      hintText: _getHint(fieldName),
                      prefixIcon: Icon(_getIcon(fieldName),
                          color: kPrimaryColor, size: 20),
                      border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12)),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide:
                            const BorderSide(color: kPrimaryColor, width: 2),
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
            backgroundColor: kPrimaryColor,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12)),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          ),
        ),
      ],
    );
  }

  String _getHint(String field) {
    String f = field.toLowerCase();
    if (f.contains("prix") || f.contains("montant") || f.contains("valeur")) return "ex: 500000";
    if (f.contains("lettres")) return "ex: Cinq cent mille";
    if (f.contains("quartier")) return "ex: Tevragh Zeina";
    if (f.contains("moughataa")) return "ex: Sebkha";
    if (f.contains("parcelle") || f.contains("terrain")) return "ex: 1234 A";
    if (f.contains("surface")) return "ex: 200";
    if (f.contains("société") || f.contains("dénomination")) return "ex: SARL MAURI-CORP";
    if (f.contains("registre")) return "ex: RC 12345/B";
    if (f.contains("parts")) return "ex: 50";
    if (f.contains("wali") || f.contains("tuteur")) return "Nom du tuteur légal";
    if (f.contains("témoin")) return "Nom complet du témoin";
    if (f.contains("marque") || f.contains("modèle")) return "ex: Toyota Hilux";
    return "";
  }

  IconData _getIcon(String field) {
    String f = field.toLowerCase();
    if (f.contains("prix") || f.contains("montant") || f.contains("valeur")) return Icons.payments_outlined;
    if (f.contains("lettres")) return Icons.abc_outlined;
    if (f.contains("quartier") || f.contains("moughataa")) return Icons.location_city_outlined;
    if (f.contains("parcelle") || f.contains("terrain")) return Icons.landscape_outlined;
    if (f.contains("société")) return Icons.business_outlined;
    if (f.contains("registre")) return Icons.app_registration_outlined;
    if (f.contains("parts")) return Icons.pie_chart_outline;
    if (f.contains("wali") || f.contains("tuteur") || f.contains("témoin")) return Icons.person_outline;
    if (f.contains("marque") || f.contains("châssis")) return Icons.directions_car_outlined;
    return Icons.edit_note_outlined;
  }
}

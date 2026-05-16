import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/language_provider.dart';

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
      "Numéro du permis d'occuper": "permis_num",
      "Date du permis d'occuper": "permis_date",
      "Numéro de parcelle / Terrain": "parcelle",
      "Numéro de parcelle / Lot": "lot",
      "Numéro d'Ilot": "ilot",
      "Zone": "zone",
      "Superficie (m²)": "superficie",
      "Surface du terrain (m²)": "surface",
      "Numéro de Quittance": "quittance_num",
      
      // Mariage
      "Nom du Wali (Tuteur légal)": "wali",
      "Premier Témoin": "temoin1",
      "Second Témoin": "temoin2",
      "Montant de la Dot (Mahr)": "mahr",
      "État de la Dot (Payé/Différé)": "mahr_etat",
      "Conditions particulières": "conditions",
      
      // Vente Véhicule
      "Marque et Modèle du véhicule": "marque_modele",
      "Type du véhicule": "type",
      "Numéro de Châssis": "chassis",
      "Puissance fiscale": "puissance_fiscale",
      "Énergie / Carburant": "energie",
      "Nombre de places": "places",
      "Numéro d'immatriculation": "matricule",
      "Prix de vente (MRU)": "prix",
      "Date de 1ère mise en circulation": "date_premier_immat",
      "Année de mise en circulation": "annee",

      // Vente Société / Cession de parts
      "Dénomination de la société": "nom_societe",
      "Registre du Commerce": "registre_commerce",
      "Nombre de parts cédées": "parts_cedees",
      "Valeur nominale": "valeur_nominale",
      "Prix de cession (MRU)": "prix",
      "Prix en lettres": "prix_lettres",
      
      // Testament
      "Biens concernés": "biens",
      
      // Hypothèque
      "Le montant de la dette": "montant_dette",
      "La durée de remboursement": "duree_remboursement",
      "Les conditions d’exécution en cas de non-paiement": "conditions_execution",

      // Commun
      "Prix de cession": "prix",
      "Prix": "prix",
      "Date d'effet": "date_effet",
    };
  }

  @override
  Widget build(BuildContext context) {
    final lp = Provider.of<LanguageProvider>(context);
    String titleText = lp.translate('complete_act');
    if (actType == "mariage") titleText = lp.translate('complete_mariage');
    else if (actType == "vente_immobilier") titleText = lp.translate('complete_immobilier');
    else if (actType == "vente_vehicule") titleText = lp.translate('complete_vehicule');
    else if (actType == "vente_societe") titleText = lp.translate('complete_societe');
    else if (actType == "testament") titleText = lp.translate('complete_testament');
    else if (actType == "hypotheque") titleText = lp.translate('complete_hypotheque');

    return Directionality(
      textDirection: lp.isArabic ? TextDirection.rtl : TextDirection.ltr,
      child: AlertDialog(
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
                    "⚠️ ${controllers.length} ${lp.translate('missing_info_desc')}",
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
                      textAlign: lp.isArabic ? TextAlign.right : TextAlign.left,
                      decoration: InputDecoration(
                        labelText: _translateFieldName(fieldName, lp),
                        hintText: _getHint(fieldName, lp),
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
            child: Text(lp.translate('later'),
                style: const TextStyle(color: Colors.grey)),
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
            label: Text(lp.translate('finalize_button')),
            style: ElevatedButton.styleFrom(
              backgroundColor: kPrimaryColor,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            ),
          ),
        ],
      ),
    );
  }

  String _translateFieldName(String field, LanguageProvider lp) {
    if (!lp.isArabic) return field;
    
    // Mapping manuel simple pour les labels de champs
    if (field.contains("permis d'occuper") && field.contains("Numéro")) return "رقم إذن الإشغال";
    if (field.contains("permis d'occuper") && field.contains("Date")) return "تاريخ إذن الإشغال";
    if (field.contains("Prix") || field.contains("Montant")) return "السعر / المبلغ (أوقية)";
    if (field.contains("Parcelle") || field.contains("Terrain")) return "رقم القطعة الأرضية";
    if (field.contains("Lot")) return "الدفعة (Lot)";
    if (field.contains("Ilot")) return "المربع (Ilot)";
    if (field.contains("Zone")) return "المنطقة";
    if (field.contains("Superficie") || field.contains("Surface")) return "المساحة (م²)";
    if (field.contains("Quittance")) return "رقم المخالصة";
    if (field.contains("Wali")) return "اسم الولي";
    if (field.contains("Témoin")) return "اسم الشاهد";
    if (field.contains("Dot")) return "المهر";
    if (field.contains("État de la Dot")) return "حالة المهر (مدفوع/مؤجل)";
    if (field.contains("Conditions")) return "شروط خاصة";
    if (field.contains("Marque")) return "الماركة والطراز";
    if (field.contains("Châssis")) return "رقم الهيكل (VIN)";
    if (field.contains("Immatriculation")) return "رقم التسجيل";
    if (field.contains("Année")) return "سنة الصنع";
    if (field.contains("Dénomination")) return "اسم الشركة";
    if (field.contains("Parts")) return "عدد الحصص";
    if (field.contains("Biens")) return "الممتلكات المعنية";
    if (field.contains("dette")) return "مبلغ الدين";
    if (field.contains("remboursement")) return "مدة السداد";
    
    return field;
  }

  String _getHint(String field, LanguageProvider lp) {
    String f = field.toLowerCase();
    if (f.contains("prix") || f.contains("montant") || f.contains("valeur")) return lp.isArabic ? "مثال: 500000" : "ex: 500000";
    if (f.contains("lettres")) return lp.isArabic ? "مثال: خمس مئة ألف" : "ex: Cinq cent mille";
    if (f.contains("quartier")) return lp.isArabic ? "مثال: تفرغ زينة" : "ex: Tevragh Zeina";
    if (f.contains("moughataa")) return lp.isArabic ? "مثال: السبخة" : "ex: Sebkha";
    if (f.contains("parcelle") || f.contains("terrain")) return lp.isArabic ? "مثال: 1234 أ" : "ex: 1234 A";
    if (f.contains("surface")) return lp.isArabic ? "مثال: 200" : "ex: 200";
    if (f.contains("société") || f.contains("dénomination")) return lp.isArabic ? "مثال: شركة موريتانيا ش.م.م" : "ex: SARL MAURI-CORP";
    if (f.contains("registre")) return lp.isArabic ? "مثال: RC 12345/B" : "ex: RC 12345/B";
    if (f.contains("parts")) return lp.isArabic ? "مثال: 50" : "ex: 50";
    if (f.contains("wali") || f.contains("tuteur")) return lp.isArabic ? "الاسم الكامل للولي" : "Nom du tuteur légal";
    if (f.contains("témoin")) return lp.isArabic ? "الاسم الكامل للشاهد" : "Nom complet du témoin";
    if (f.contains("marque") || f.contains("modèle")) return lp.isArabic ? "مثال: تويوتا هايلوكس" : "ex: Toyota Hilux";
    if (f.contains("biens")) return lp.isArabic ? "مثال: منزل، أرض، سيارة..." : "ex: Maison, terrain, car...";
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
    if (f.contains("biens")) return Icons.account_balance_wallet_outlined;
    return Icons.edit_note_outlined;
  }
}


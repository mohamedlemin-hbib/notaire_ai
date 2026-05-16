
import sys
import os
import re

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.services.rag_service import generate_notarial_draft, identify_missing_fields

def test_repro():
    template_text = """
- Marque/Modèle : ........................
- Type : ........................
- N° de Châssis : ........................
- Puissance fiscale : ........................
- Énergie : ........................
- Places assises autorisées : ........................
- Date de 1ère mise en circulation : ........................
- Numéro d'immatriculation : ........................
"""
    
    # Mock data from OCR
    completion_data = {
        'marque': 'TOYOTA',
        'marque_modele': 'TOYOTA HILUX',
        'type': 'PICKUP',
        'chassis': 'ABC1234567890XYZ',
        'puissance_fiscale': '10CV',
        'energie': 'GASOIL',
        'places': '5',
        'date_premier_immat': '01/01/2020',
        'immatriculation': '1234AA00'
    }
    
    parties_info = {
        'vendeur': {'nom': 'AIDALHA', 'prenom': 'Ahmed salem', 'nni': '9930098939', 'date_naissance': '03/03/2005', 'lieu_naissance': 'Teyaret'},
        'acheteur': {'nom': 'ABDEL KADER', 'prenom': 'Myna', 'nni': '5767899070', 'date_naissance': '02/12/1994', 'lieu_naissance': 'Teyaret'}
    }
    
    # We need to mock the file opening in rag_service or just test the logic here
    # Since we want to test the REAL function, let's make sure the template file exists and has content
    
    draft = generate_notarial_draft(
        act_type="vente_vehicule",
        parties_info=parties_info,
        special_clauses="Marque: TOYOTA. Modèle: HILUX.",
        notary_name="Maître Test",
        notary_bureau="Bureau Test",
        completion_data=completion_data
    )
    
    print("--- DRAFT OUTPUT ---")
    print(draft)
    print("--- END DRAFT ---")

    # Check if placeholders are still there
    placeholders = [
        "Marque/Modèle", "Type", "N° de Châssis", "Puissance fiscale",
        "Énergie", "Places assises autorisées", "Date de 1ère mise en circulation",
        "Numéro d'immatriculation"
    ]
    
    for p in placeholders:
        if "........" in draft and p in draft:
            # Check if the line containing p still has dots
            lines = draft.split('\n')
            for line in lines:
                if p in line and "...." in line:
                    print(f"FAILED: Placeholder for '{p}' still exists: {line}")

if __name__ == "__main__":
    test_repro()

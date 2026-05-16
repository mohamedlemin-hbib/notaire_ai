
import re
import unicodedata

def _strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                 if unicodedata.category(c) != 'Mn')

def re_replace_dots(label, value, text):
    label_no_accent = _strip_accents(label)
    # Pattern to match: optional newline/start, optional bullet, label, colon, then 2+ dots
    pattern = r"(?:^|\n)\s*[-•*]?\s*(?:" + re.escape(label) + "|" + re.escape(label_no_accent) + r")\s*[:]\s*\.{2,}"
    
    # We want to keep the newline if we matched it, or add one if it was start of string
    # Actually, let's keep it simple: replace the whole match with the new line
    replacement = f"\n- {label} : {value}"
    
    print(f"DEBUG: Trying to match label '{label}' with value '{value}'")
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match:
        print(f"DEBUG: MATCH FOUND for '{label}': '{match.group(0)}'")
    else:
        print(f"DEBUG: NO MATCH for '{label}'")
        
    return re.sub(pattern, replacement, text, flags=re.IGNORECASE)

template = """- Marque/Modèle : ........................
- Type : ........................
- N° de Châssis : ........................
- Puissance fiscale : ........................
- Énergie : ........................
- Places assises autorisées : ........................
- Date de 1ère mise en circulation : ........................
- Numéro d'immatriculation : ........................"""

res = template
res = re_replace_dots("Marque/Modèle", "TOYOTA", res)
res = re_replace_dots("Type", "PICKUP", res)
res = re_replace_dots("N° de Châssis", "ABC123456", res)

print("\n--- RESULT ---")
print(res)

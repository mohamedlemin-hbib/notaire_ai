
import arabic_reshaper
from bidi.algorithm import get_display

text = "الجمهورية الإسلامية الموريتانية"
reshaped = arabic_reshaper.reshape(text)
bidi_text = get_display(reshaped)

print(f"Original: {text}")
print(f"Bidi: {bidi_text}")

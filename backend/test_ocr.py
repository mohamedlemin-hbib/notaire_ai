import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

from app.services.ocr_service import extract_info_from_ids_batch
from PIL import Image
import io

def generate_fake_image():
    img = Image.new('RGB', (100, 100), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

b1 = generate_fake_image()
b2 = generate_fake_image()

print("Appel de l'API Gemini OCR...")
try:
    result = extract_info_from_ids_batch(b1, b2)
    print("Résultat :")
    print(result)
except Exception as e:
    print(f"FAILED: {e}")

import asyncio
from app.services.ocr_service import extract_info_from_permis_occuper
from PIL import Image
import io

def create_dummy_image():
    img = Image.new('RGB', (800, 600), color = (73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()

dummy_bytes = create_dummy_image()
res = extract_info_from_permis_occuper(dummy_bytes)
print("Result:", res)

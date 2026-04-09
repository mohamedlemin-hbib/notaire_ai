import sys
import os
import json
import io
from PIL import Image

# Add root to path to allow imports from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create a small valid image in memory
buf = io.BytesIO()
Image.new('RGB', (10, 10)).save(buf, format='JPEG')
img_bytes = buf.getvalue()

from backend.app.services.ocr_service import _get_image_hash, _save_to_cache, extract_info_from_ids_batch

def test_cache():
    print("Starting cache verification test...")
    
    # Fake data
    v_bytes = img_bytes + b"v"
    a_bytes = img_bytes + b"a"
    
    h = _get_image_hash(v_bytes, a_bytes)
    print(f"Generated Hash: {h}")
    
    fake_data = {
        "vendeur": {"nom": "CACHE_WORKS", "prenom": "YES"},
        "acheteur": {"nom": "CACHE_WORKS", "prenom": "YES"}
    }
    
    # Save to cache manually
    print("Saving fake data to cache...")
    _save_to_cache(h, fake_data)
    
    # Try to retrieve via service
    print("Calling service...")
    # This should hit the cache BEFORE calling PIL or Gemini
    result = extract_info_from_ids_batch(v_bytes, a_bytes)
    
    print(f"Result: {result}")
    
    if result.get("vendeur", {}).get("nom") == "CACHE_WORKS":
        print("\n✅ SUCCESS: Cache hit detected and data retrieved correctly!")
    else:
        print("\n❌ FAILURE: Cache was not used or data is incorrect.")

if __name__ == "__main__":
    test_cache()

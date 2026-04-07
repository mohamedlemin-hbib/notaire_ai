import sys

def test_import(module_name):
    try:
        __import__(module_name)
        print(f"OK: {module_name}")
    except ImportError as e:
        print(f"FAIL: {module_name} ({e})")
    except Exception as e:
        print(f"ERR: {module_name} ({e})")

print("Python Path:", sys.path)
print("\nTesting imports:")
test_import("google.generativeai")
test_import("google.genai")
test_import("langchain_google_genai")

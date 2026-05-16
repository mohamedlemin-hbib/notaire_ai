
import os

search_dir = r"c:\Users\Mdhamed\projet_notaire_ia\backend"
search_str = "✓"

for root, dirs, files in os.walk(search_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if search_str in content:
                        print(f"FOUND IN {path}")
            except Exception as e:
                print(f"Error reading {path}: {e}")

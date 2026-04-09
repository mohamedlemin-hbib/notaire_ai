import uvicorn
import sys
import os

if __name__ == "__main__":
    print("Starting backend...")
    sys.stdout.flush()
    try:
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
    except Exception as e:
        print(f"Error: {e}")
        sys.stdout.flush()

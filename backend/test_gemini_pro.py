import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-pro-latest",
        contents="Hi"
    )
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)

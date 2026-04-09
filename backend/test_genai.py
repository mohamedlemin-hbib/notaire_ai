import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
try:
    print("API Key loaded:", bool(os.getenv("GOOGLE_API_KEY")))
    client = genai.Client()
    print("Client initialized")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='say hi'
    )
    print("Success:", response.text)
except Exception as e:
    print("Error:", str(e))

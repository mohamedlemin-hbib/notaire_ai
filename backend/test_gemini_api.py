import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

try:
    response = model.generate_content("Convert 19000 to French letters for a notary act in Mauritania.")
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)

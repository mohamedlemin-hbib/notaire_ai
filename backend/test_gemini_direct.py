import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key found: {api_key[:5]}...{api_key[-5:]}" if api_key else "No API Key")

llm = ChatGoogleGenerativeAI(
    google_api_key=api_key,
    model="gemini-2.0-flash"
)

try:
    response = llm.invoke("Bonjour, es-tu prêt pour rédiger des actes notariés ?")
    print("\nRéponse de Gemini :")
    print(response.content)
except Exception as e:
    print(f"\nErreur Gemini : {e}")

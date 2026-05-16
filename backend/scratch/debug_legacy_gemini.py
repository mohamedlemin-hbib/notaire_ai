import os
import google.generativeai as genai
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
print(f"Key found: {settings.GOOGLE_API_KEY[:8]}...")

genai.configure(api_key=settings.GOOGLE_API_KEY)

try:
    # Simple list models to test key with legacy SDK
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Success! Found model: {m.name}")
            break
except Exception as e:
    print(f"Error: {e}")

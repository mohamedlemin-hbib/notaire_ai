import os
from google import genai
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
print(f"Key found: {settings.GOOGLE_API_KEY[:8]}...")

try:
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    # Simple list models to test key
    models = client.models.list()
    print("Success! Successfully listed models.")
except Exception as e:
    print(f"Error: {e}")

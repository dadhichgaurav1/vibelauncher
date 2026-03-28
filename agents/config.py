import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# X / Twitter
X_CONSUMER_KEY = os.getenv("X_CONSUMER_KEY", "")
X_CONSUMER_SECRET = os.getenv("X_CONSUMER_SECRET", "")
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN", "")
X_CALLBACK_URL = os.getenv("X_CALLBACK_URL", "http://localhost:3000/api/auth/x/callback")

# App
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vibelauncher.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")

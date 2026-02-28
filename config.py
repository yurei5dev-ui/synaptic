import os
from dotenv import load_dotenv

load_dotenv()

MODE = "groq"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

OLLAMA_MODEL = "gemma3:4b"

KAI_NAME = "KAI"
KAI_PERSONALITY = "You are KAI, a smart, chill and helpful AI assistant. Keep responses short and natural, like talking to a friend."
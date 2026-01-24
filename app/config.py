import os
from dotenv import load_dotenv

load_dotenv()


OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
WHISPER_MODEL = os.getenv("WHISPER_MODEL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE")

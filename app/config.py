import os
from dotenv import load_dotenv
import logging

from pathlib import Path

load_dotenv()

# LLM config
CONVERSATIONAL_LLM = os.getenv("CONVERSATIONAL_LLM")
WHISPER_MODEL = os.getenv("WHISPER_MODEL")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE")

# Tokens/ Log config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL", logging.INFO)

# Folders config
TEMP_DIR = Path("data/temp_audio")
TEMP_DIR.mkdir(exist_ok=True, parents=True)
DB_PATH = Path("data/conversations.db")
SERIALIZED_DATA_PATH = Path("data/conversations.json")

# Storage config
# Max number of messages to store per chat session (hot cache)
MAX_CONVERSATION_TURNS = 10 * 2  # (user + assistant = 2 messages per turn)

import os
from dotenv import load_dotenv
import logging

from pathlib import Path

load_dotenv()

# Models config
CONVERSATIONAL_LLM = os.getenv("CONVERSATIONAL_LLM")
WHISPER_MODEL = os.getenv("WHISPER_MODEL")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE")

# Tokens/ Log config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL", logging.INFO)

# Folders config
TEMP_DIR = Path("data/temp_audio")
TEMP_DIR.mkdir(exist_ok=True, parents=True)

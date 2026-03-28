from telegram import Update
from telegram.ext import ContextTypes

from app.llm.conversation_memory import ConversationReminder, RapidMemoryManager
from app.pipelines.text_pipeline import TextPipeline
from app.pipelines.voice_pipeline import AudioPipeline
from app.utils.conversation_db import ConversationDB
from app.logging import get_logger

logger = get_logger(__name__)
text_pipeline = TextPipeline()
voice_pipeline = AudioPipeline()

# Cache to store the latest agent voice response transcribed per user
latest_agent_voice_response: dict[str, str] = {}


def set_latest_agent_voice_response(user_id: int, audio_text: str) -> None:
    latest_agent_voice_response[str(user_id)] = audio_text


def get_latest_agent_voice_response(user_id: int) -> str | None:
    return latest_agent_voice_response.get(str(user_id))


def get_updated_memory(chat_id: str, db: ConversationDB) -> ConversationReminder:
    """Helper function to update the in-memory conversation context for a given chat_id.

    :chat_id: Unique identifier for the chat (e.g., user ID)
    :db: Instance of the ConversationDB to access stored conversations
    :returns: Updated ConversationReminder instance with the conversation history loaded
    """
    chat_hot_memory: ConversationReminder = RapidMemoryManager.get_memory(chat_id=chat_id)

    if db.is_new_conversation(chat_id):
        chat_hot_memory.clear()
        conv = db.get_conversation(chat_id)
        if conv and conv["messages"]:
            for msg in conv["messages"]:
                if msg["role"] == "user":
                    chat_hot_memory.add_user_message(msg["content"])
                elif msg["role"] == "assistant":
                    chat_hot_memory.add_assistant_message(msg["content"])

    return chat_hot_memory


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued.

    :update: Incoming update from Telegram
    :context: Context for the callback
    """
    await update.message.reply_text(
        f"Olá {update.message.from_user.first_name}! Sou Lisa, sua parceira de idiomas.\n"
        "Sobre o que vamos conversar hoje? Pode me mandar um áudio se quiser!\n"
        "Comandos disponíveis:\n\n"
        "/start - Iniciar a conversa\n"
        "/transcribe - Transcrever a última resposta de voz\n"
    )


async def on_shutdown(app) -> None:
    """Cleanup resources on shutdown"""
    await text_pipeline.llm.close()
    await voice_pipeline.llm.close()

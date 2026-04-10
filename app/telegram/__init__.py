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

# Cache to store the latest voice response
latest_agent_voice_response: dict[str, str] = {}
latest_user_voice_input: dict[str, str] = {}


def set_latest_agent_voice_response(user_id: int, audio_text: str) -> None:
    latest_agent_voice_response[str(user_id)] = audio_text


def get_latest_agent_voice_response(user_id: int) -> str | None:
    return latest_agent_voice_response.get(str(user_id))


def set_latest_user_voice_input(user_id: int, audio_text: str) -> None:
    latest_user_voice_input[str(user_id)] = audio_text


def get_latest_user_voice_input(user_id: int) -> str | None:
    return latest_user_voice_input.get(str(user_id))


def get_updated_memory(chat_id: str, db: ConversationDB) -> ConversationReminder:
    """Helper function to update the in-memory conversation context for a given chat_id.

    :chat_id: Unique identifier for the chat (e.g., user ID)
    :db: Instance of the ConversationDB to access stored conversations
    :returns: Updated ConversationReminder instance with the conversation history loaded
    """
    chat_hot_memory: ConversationReminder = RapidMemoryManager.get_memory(chat_id=chat_id)

    if db.is_new_conversation(chat_id):
        chat_hot_memory.clear()
        return chat_hot_memory

    if not chat_hot_memory.get_messages():
        conv = db.get_conversation(chat_id)
        if conv and conv["messages"]:
            for msg in conv["messages"]:
                if msg["role"] == "user":
                    chat_hot_memory.add_user_message(msg["content"])
                elif msg["role"] == "assistant":
                    chat_hot_memory.add_assistant_message(msg["content"])

    return chat_hot_memory


def persist_conversation_context(chat_id: str, db: ConversationDB, chat_hot_memory: ConversationReminder) -> None:
    """Helper function to persist the conversation context for a given chat_id.

    :chat_id: Unique identifier for the chat (e.g., user ID)
    :db: Instance of the ConversationDB to access stored conversations
    :chat_hot_memory: ConversationReminder instance containing the conversation history to be persisted
    """
    existing = db.get_conversation(chat_id)
    existing_messages = existing["messages"] if existing else []
    new_messages = chat_hot_memory.get_messages()

    if len(new_messages) > len(existing_messages):
        delta = new_messages[len(existing_messages) :]
    else:
        delta = new_messages[-2:]  # Get only the latest iteration

    merged_msgs = existing_messages + delta
    db.save_conversation(chat_id, merged_msgs)
    logger.info(f"Updated conversation persistence for chat_id: {chat_id}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, evaluation_mode: bool) -> None:
    """Send a welcome message when the /start command is issued.

    :update: Incoming update from Telegram
    :context: Context for the callback
    """
    if evaluation_mode:
        context.user_data["started_evaluation"] = True

        await update.message.reply_text(
            "Hi! You just started our evaluation mode.\n\n"
            "In this mode, you'll be guided through an assisted assessment of your preferred language.\n"
            "We highly encourage you to opt for voice interactions "
            "to fully engage with the assessment and have a better experience.\n\n"
            "To proceed, just send me a voice message in the language you're learning, introducing yourself. "
            "Don't worry about making it perfect - just speak naturally, and I'll take care of the rest!\n\n"
        )
    else:
        await update.message.reply_text(
            f"Olá {update.message.from_user.first_name}! Sou Lisa, sua parceira de idiomas.\n"
            "Sobre o que vamos conversar hoje? Pode me mandar um áudio se quiser!\n"
            "Comandos disponíveis:\n\n"
            "/start - Iniciar a conversa\n"
            "/whatYouSaid - Transcrever a última resposta de voz\n"
            "/whatISaid - Transcrever o que você disse\n"
        )


async def on_shutdown(app) -> None:
    """Cleanup resources on shutdown"""
    await text_pipeline.llm.close()
    await voice_pipeline.llm.close()

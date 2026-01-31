from telegram import Update
from telegram.ext import ContextTypes

from app.pipelines.text_pipeline import TextPipeline
from app.pipelines.voice_pipeline import AudioPipeline
from app.logging import get_logger

logger = get_logger(__name__)
text_pipeline = TextPipeline()
voice_pipeline = AudioPipeline()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued.

    :update: Incoming update from Telegram
    :context: Context for the callback
    """
    await update.message.reply_text(
        f"Olá {update.message.from_user.first_name}! Sou Lisa, sua parceira de idiomas.\n"
        "Sobre o que vamos conversar hoje? Pode me mandar um áudio se quiser!"
    )


async def on_shutdown(app) -> None:
    """Cleanup resources on shutdown"""
    await text_pipeline.llm.close()
    await voice_pipeline.llm.close()

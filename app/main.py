from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.pipelines.voice_pipeline import AudioConversationPipeline
from app.config import TELEGRAM_BOT_TOKEN, TEMP_DIR
from app.logging import get_logger

logger = get_logger(__name__)
voice_pipeline = AudioConversationPipeline()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued.

    :update: Incoming update from Telegram
    :context: Context for the callback
    """
    await update.message.reply_text(
        "Olá! Sou Lisa, sua parceira de idiomas.\n"
        "Estou aqui pra te ajudar a praticar e melhorar suas habilidades linguísticas.\n"
        "Sobre o que quer conversar hoje? Pode me mandar um áudio se quiser!"
    )


async def on_shutdown(app) -> None:
    """Cleanup resources on shutdown"""
    await voice_pipeline.llm.close()


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice messages from users.

    :update: Incoming update from Telegram
    :context: Context for the callback
    """
    voice = update.message.voice
    if not voice:
        await update.message.reply_text("Envie uma mensagem de voz, por favor.")
        return

    # Download the user voice message
    audio_file = await context.bot.get_file(voice.file_id)
    user_input_path = TEMP_DIR / f"{voice.file_id}.ogg"
    await audio_file.download_to_drive(user_input_path)
    logger.info(f"Downloaded voice message to '{user_input_path}'")

    # Where store the output
    response_output_path = TEMP_DIR / f"response_{voice.file_id}_response.ogg"

    try:
        # Pipeline processing
        result = await voice_pipeline.process_audio_conversation(user_input_path, response_output_path)
        await update.message.reply_voice(voice=result["synthesized_audio_path"])
        logger.info(
            f"=> Processed voice message from user '{update.message.from_user.id}'\n"
            f"=> Input text: '{result['user_input_text']}'\n"
            f"=> Response text: '{result['model_output_text']}'\n"
        )
    except Exception as err:
        await update.message.reply_text(
            "Tivemos um erro durante o processamento da sua mensagem. Por favor, tente novamente."
        )
        logger.error(f"Error processing voice message: {err}")

    user_input_path.unlink(missing_ok=True)
    response_output_path.unlink(missing_ok=True)


def main() -> None:
    """Main function to start the Telegram bot."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Commands Handlers
    app.add_handler(CommandHandler("start", start))

    # Voice message handler
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Start bot
    app.post_shutdown(on_shutdown)
    app.run_polling()


if __name__ == "__main__":
    main()

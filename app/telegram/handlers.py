from telegram import Update
from telegram.ext import ContextTypes

from app.config import TEMP_DIR

from . import (
    logger,
    text_pipeline,
    voice_pipeline,
    set_latest_agent_voice_response,
    get_latest_agent_voice_response,
)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice messages from users.

    :update: Incoming update from Telegram
    :context: Context for the callback
    """
    voice = update.message.voice

    # Download the user voice message
    audio_file = await context.bot.get_file(voice.file_id)
    user_input_path = TEMP_DIR / f"{voice.file_id}.ogg"
    await audio_file.download_to_drive(user_input_path)
    logger.info(f"Downloaded voice message to '{user_input_path}'")

    # Where store the output
    response_output_path = TEMP_DIR / f"response_{voice.file_id}_response.wav"

    try:
        # Voice Pipeline processing
        result = await voice_pipeline.process_conversation(user_input_path, response_output_path)
        await update.message.reply_voice(voice=result["synthesized_audio_path"])

        # Store the latest agent voice response path for this user
        set_latest_agent_voice_response(update.message.from_user.id, result["model_output_text"])

        logger.info(
            f"=> Processed voice message from user '{update.message.from_user.id}'\n"
            f"=> Input text: '{result['user_input_text']}'\n"
            f"=> Response text: '{result['model_output_text']}'\n"
        )
    except Exception as err:
        await update.message.reply_text(
            "Tivemos um erro durante o processamento da sua mensagem. Por favor, tente novamente."
        )
        logger.error(f"Error processing voice message: {err}", exc_info=True)

    user_input_path.with_suffix(".wav").unlink(missing_ok=True)
    response_output_path.unlink(missing_ok=True)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages from users.

    :update: Incoming update from Telegram
    :context: Context for the callback
    """
    user_input_text = update.message.text

    # Process the text input
    result = await text_pipeline.process_conversation(user_input_text)
    await update.message.reply_text(result["model_output_text"])
    logger.info(
        f"=> Processed text message from user '{update.message.from_user.id}'\n"
        f"=> Input text: '{result['user_input_text']}'\n"
        f"=> Response text: '{result['model_output_text']}'\n"
    )


async def handle_transcription_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /transcribe command to transcribe the latest agent voice response.

    :update: Incoming update from Telegram
    :context: Context for the callback
    """
    user_id = update.message.from_user.id
    latest_response_text = get_latest_agent_voice_response(user_id)

    if latest_response_text:
        await update.message.reply_text(latest_response_text)
    else:
        await update.message.reply_text("Desculpe, não tenho uma resposta de voz recente para transcrever.")

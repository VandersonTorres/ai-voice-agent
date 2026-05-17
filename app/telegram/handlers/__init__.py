from app.telegram import (
    get_latest_agent_voice_response,
    get_latest_user_voice_input,
)
from telegram import Update
from telegram.ext import ContextTypes

RESPONSE_AUDIO_PATH_NAME = "response_{file_id}_response.wav"


async def block_until_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not context.user_data.get("started_evaluation"):
        await update.message.reply_text("Envie '/start' para iniciar sua avaliação e desbloquear recursos de interação")
        return True

    return False


async def handle_what_agent_said(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /whatYouSaid command to transcribe the latest agent voice response.

    :update: Incoming update from Telegram
    :context: Context for the callback
    """
    user_id = update.message.from_user.id
    latest_response_text = get_latest_agent_voice_response(user_id)

    if latest_response_text:
        await update.message.reply_text(f"I said:\n{latest_response_text}")
    else:
        await update.message.reply_text("Sorry, I don't have a recent voice response to transcribe.")


async def handle_what_user_said(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /whatISaid command to transcribe the latest user voice response.

    :update: Incoming update from Telegram
    :context: Context for the callback
    """
    user_id = update.message.from_user.id
    latest_response_text = get_latest_user_voice_input(user_id)

    if latest_response_text:
        await update.message.reply_text(f"You said:\n{latest_response_text}")
    else:
        await update.message.reply_text("Sorry, I couldn't access your last voice input.")

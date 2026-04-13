from telegram import Update
from telegram.ext import ContextTypes

from app.config import TEMP_DIR
from app.utils.conversation_db import ConversationDB

from . import (
    logger,
    text_pipeline,
    voice_pipeline,
    set_latest_agent_voice_response,
    set_latest_user_voice_input,
    get_latest_agent_voice_response,
    get_latest_user_voice_input,
    get_updated_memory,
    persist_conversation_context,
)

RESPONSE_AUDIO_PATH_NAME = "response_{file_id}_response.wav"


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming voice messages from users.

    :update: Incoming update from Telegram
    :context: Context for the callback
    """
    # Download the user voice message
    voice = update.message.voice
    audio_file = await context.bot.get_file(voice.file_id)
    user_input_path = TEMP_DIR / f"{voice.file_id}.ogg"
    await audio_file.download_to_drive(user_input_path)
    logger.info(f"Downloaded voice message to '{user_input_path}'")

    # Update conversation memory with history from DB
    chat_id = str(update.message.from_user.id)
    db = ConversationDB()
    profile = db.get_profile(chat_id)
    chat_hot_memory = get_updated_memory(chat_id, db)

    # Process the voice input and Persist conversation context after processing
    response_output_path = TEMP_DIR / RESPONSE_AUDIO_PATH_NAME.format(file_id=voice.file_id)
    result = await voice_pipeline.process_conversation(
        user_input_audio_path=user_input_path,
        output_audio_path=response_output_path,
        chat_memory=chat_hot_memory,
        user_profile=profile,
    )
    # Persist conversation context and profile after processing
    persist_conversation_context(chat_id, db, chat_hot_memory)
    updated_profile = result.get("parsed_profile") or {}
    if updated_profile:
        if not updated_profile["name"]:
            updated_profile["name"] = update.message.from_user.first_name

        db.save_profile(chat_id, updated_profile)

    try:
        # Reply
        await update.message.reply_voice(voice=result["synthesized_audio_path"])
        set_latest_agent_voice_response(update.message.from_user.id, result["model_output_text"])
        set_latest_user_voice_input(update.message.from_user.id, result["user_input_text"])
        logger.info(
            f"=> Processed voice message from user '{update.message.from_user.id}'\n"
            f"=> Input text: '{result['user_input_text']}'\n"
            f"=> Response text: '{result['model_output_text']}'\n"
        )
    except Exception as err:
        await update.message.reply_text(f"Vou responder por texto dessa vez.\n\n{result['model_output_text']}")
        logger.error(f"Error processing voice message. Response sent via text. Details: {err}", exc_info=True)

    # Cleanup temporary audio files
    user_input_path.with_suffix(".wav").unlink(missing_ok=True)
    response_output_path.unlink(missing_ok=True)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages from users.

    :update: Incoming update from Telegram
    :context: Context for the callback
    """
    # Update conversation memory with history from DB
    chat_id = str(update.message.from_user.id)
    db = ConversationDB()
    profile = db.get_profile(chat_id)
    chat_hot_memory = get_updated_memory(chat_id, db)

    # Process the text input and Persist conversation context after processing
    user_input_text = update.message.text
    result = await text_pipeline.process_conversation(
        user_input_text, chat_memory=chat_hot_memory, user_profile=profile
    )

    # Persist conversation context and profile after processing
    persist_conversation_context(chat_id, db, chat_hot_memory)
    updated_profile = result.get("parsed_profile") or {}
    if updated_profile:
        if not updated_profile.get("name"):
            updated_profile["name"] = update.message.from_user.first_name

        db.save_profile(chat_id, updated_profile)

    if result.get("should_convert_to_audio") is True:
        try:
            response_output_path = TEMP_DIR / RESPONSE_AUDIO_PATH_NAME.format(file_id=update.message.message_id)
            audio_path = await voice_pipeline.synthesize_audio_output(
                model_output_text=result["model_output_text"],
                output_audio_path=response_output_path,
            )
            await update.message.reply_voice(voice=audio_path)
            set_latest_agent_voice_response(update.message.from_user.id, result["model_output_text"])
            logger.info(
                f"=> Processed text message from user '{update.message.from_user.id}' with audio response\n"
                f"=> Input text: '{result['user_input_text']}'\n"
                f"=> Response text: '{result['model_output_text']}'\n"
            )
            audio_path.unlink(missing_ok=True)
        except Exception as err:
            await update.message.reply_text(f"Vou responder por texto dessa vez.\n\n{result['model_output_text']}")
            logger.error(f"Error processing voice message. Response sent via text. Details: {err}", exc_info=True)

        return

    # Reply Text
    await update.message.reply_text(result["model_output_text"])
    logger.info(
        f"=> Processed text message from user '{update.message.from_user.id}'\n"
        f"=> Input text: '{result['user_input_text']}'\n"
        f"=> Response text: '{result['model_output_text']}'\n"
    )


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

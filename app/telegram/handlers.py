from pathlib import Path
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from app.config import TEMP_DIR
from app.llm.conversation_memory import ConversationReminder
from app.utils.conversation_db import ConversationDB

from . import (
    logger,
    text_pipeline,
    voice_pipeline,
    evaluation_voice_pipeline,
    set_latest_agent_voice_response,
    set_latest_user_voice_input,
    get_latest_agent_voice_response,
    get_latest_user_voice_input,
    get_updated_memory,
    persist_conversation_context,
)

RESPONSE_AUDIO_PATH_NAME = "response_{file_id}_response.wav"


async def _block_until_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not context.user_data.get("started_evaluation"):
        await update.message.reply_text("Envie '/start' para iniciar sua avaliação e desbloquear recursos de interação")
        return True

    return False


async def _handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict[str, Any]:
    """Handle incoming voice messages from users.

    :update: Incoming update from Telegram
    :context: Context for the callback
    :returns: A dict with the following keys:
        - user_input_path
        - response_output_path
        - chat_hot_memory
        - profile
        - chat_id
        - db
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
    return {
        "user_input_path": user_input_path,
        "response_output_path": response_output_path,
        "chat_hot_memory": chat_hot_memory,
        "profile": profile,
        "chat_id": chat_id,
        "db": db,
    }


async def _voice_post_processing(
    update: Update,
    result: dict[str, Any],
    chat_id: str,
    db: ConversationDB,
    chat_hot_memory: ConversationReminder,
    user_input_path: Path,
    response_output_path: Path,
    is_evaluation: bool = False,
) -> None:
    """Handle the post-processing steps after receiving the result from the voice pipeline."""
    persist_conversation_context(chat_id, db, chat_hot_memory)
    updated_profile = result.get("parsed_profile") or {}
    if updated_profile:
        if not updated_profile["name"]:
            updated_profile["name"] = update.message.from_user.first_name

        db.save_profile(chat_id, updated_profile)

    try:
        # Reply
        user_input = "user_input_text" if not is_evaluation else "user_literal_text"
        await update.message.reply_voice(voice=result["synthesized_audio_path"])
        set_latest_agent_voice_response(update.message.from_user.id, result["model_output_text"])
        set_latest_user_voice_input(update.message.from_user.id, result[user_input])
        logger.info(
            f"=> Processed voice message from user '{update.message.from_user.id}'\n"
            f"=> Input text: '{result[user_input]}'\n"
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


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    voice_process_result = await _handle_voice(update, context)
    user_input_path: Path = voice_process_result["user_input_path"]
    response_output_path: Path = voice_process_result["response_output_path"]
    chat_hot_memory: ConversationReminder = voice_process_result["chat_hot_memory"]
    profile: dict[str, Any] = voice_process_result["profile"]
    chat_id: str = voice_process_result["chat_id"]
    db: ConversationDB = voice_process_result["db"]

    result = await voice_pipeline.process_conversation(
        user_input_audio_path=user_input_path,
        output_audio_path=response_output_path,
        chat_memory=chat_hot_memory,
        user_profile=profile,
    )

    await _voice_post_processing(
        update,
        result,
        chat_id,
        db,
        chat_hot_memory,
        user_input_path,
        response_output_path,
    )


async def evaluation_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _block_until_start(update, context):
        return

    # TODO: Custom processing here


async def evaluation_voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _block_until_start(update, context):
        return

    # TODO: Clean memory if first interaction in evaluation mode
    voice_process_result = await _handle_voice(update, context)
    user_input_path: Path = voice_process_result["user_input_path"]
    response_output_path: Path = voice_process_result["response_output_path"]
    chat_hot_memory: ConversationReminder = voice_process_result["chat_hot_memory"]
    profile: dict[str, Any] = voice_process_result["profile"]
    chat_id: str = voice_process_result["chat_id"]
    db: ConversationDB = voice_process_result["db"]

    result = await evaluation_voice_pipeline.process_conversation(
        user_input_audio_path=user_input_path,
        output_audio_path=response_output_path,
        chat_memory=chat_hot_memory,
        user_profile=profile,
    )

    await _voice_post_processing(
        update,
        result,
        chat_id,
        db,
        chat_hot_memory,
        user_input_path,
        response_output_path,
        is_evaluation=True,
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

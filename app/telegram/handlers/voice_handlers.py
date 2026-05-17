from pathlib import Path
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from app.config import TEMP_DIR
from app.llm.conversation_memory import ConversationReminder
from app.utils.conversation_db import ConversationDB
from app.telegram import (
    logger,
    voice_pipeline,
    set_latest_agent_voice_response,
    set_latest_user_voice_input,
    get_updated_memory,
    persist_conversation_context,
)

from . import RESPONSE_AUDIO_PATH_NAME


async def handle_voice(
    update: Update, context: ContextTypes.DEFAULT_TYPE, force_new_conversation: bool = False
) -> dict[str, Any]:
    """Handle incoming voice messages from users.

    :update: Incoming update from Telegram
    :context: Context for the callback
    :force_new_conversation: If True, forces the creation of a new conversation context
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
    chat_hot_memory = get_updated_memory(chat_id, db, force_new_conversation=force_new_conversation)

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


async def voice_post_processing(
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


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    voice_process_result = await handle_voice(update, context)
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

    await voice_post_processing(
        update,
        result,
        chat_id,
        db,
        chat_hot_memory,
        user_input_path,
        response_output_path,
    )

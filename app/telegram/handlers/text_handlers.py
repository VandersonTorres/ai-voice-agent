from telegram import Update
from telegram.ext import ContextTypes

from app.config import TEMP_DIR
from app.utils.conversation_db import ConversationDB

from app.telegram import (
    logger,
    text_pipeline,
    voice_pipeline,
    set_latest_agent_voice_response,
    get_updated_memory,
    persist_conversation_context,
)

from . import RESPONSE_AUDIO_PATH_NAME


async def text_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE, force_new_conversation: bool = False
) -> None:
    """Handle incoming text messages from users.

    :update: Incoming update from Telegram
    :context: Context for the callback
    :force_new_conversation: If True, forces the creation of a new conversation context
    """
    # Update conversation memory with history from DB
    chat_id = str(update.message.from_user.id)
    db = ConversationDB()
    profile = db.get_profile(chat_id)
    chat_hot_memory = get_updated_memory(chat_id, db, force_new_conversation=force_new_conversation)

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

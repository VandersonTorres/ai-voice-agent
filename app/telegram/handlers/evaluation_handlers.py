from pathlib import Path
from typing import Any, Callable

from jmespath import search as jsearch
from telegram import Update
from telegram.ext import ContextTypes

from app.llm.conversation_memory import ConversationReminder
from app.utils.conversation_db import ConversationDB
from app.telegram import evaluation_voice_pipeline, logger
from app.telegram.handlers.voice_handlers import handle_voice, voice_post_processing

from . import block_until_start


async def _handle_voice_chat_phase(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs: Any) -> None:
    """Handle voice chat interactions for phase 1 and collect metrics for evaluation"""
    if update.message.text:
        # Doesn't allow text input during phase 1 of evaluation.
        await update.message.reply_text(
            "Desculpe, mas não posso aceitar mensagens de texto nessa fase. Por favor, envie uma mensagem de voz."
        )
        return

    force_new_conversation = kwargs.get("force_new_conversation", False)
    voice_process_result = await handle_voice(update, context, force_new_conversation=force_new_conversation)
    user_input_path: Path = voice_process_result["user_input_path"]
    response_output_path: Path = voice_process_result["response_output_path"]

    chat_hot_memory: ConversationReminder = voice_process_result["chat_hot_memory"]
    profile: dict[str, Any] = voice_process_result["profile"]
    chat_id: str = voice_process_result["chat_id"]
    db: ConversationDB = voice_process_result["db"]

    context.user_data["evaluation"]["turn_count"] += 1
    current_turn = jsearch("evaluation.turn_count", context.user_data)

    result = await evaluation_voice_pipeline.process_conversation(
        user_input_audio_path=user_input_path,
        output_audio_path=response_output_path,
        chat_memory=chat_hot_memory,
        user_profile=profile,
        current_turn=current_turn,
    )

    await voice_post_processing(
        update,
        result,
        chat_id,
        db,
        chat_hot_memory,
        user_input_path,
        response_output_path,
        is_evaluation=True,
    )

    should_finish = result.get("evaluation_ready", False)
    if should_finish:
        await update.message.reply_text("Fase 1 concluída! Prepare para a próxima fase")
        # Set next phase to evaluation (phase 2) and reset turn count for next phase
        context.user_data["evaluation"]["phase"] = "phase_2"
        context.user_data["evaluation"]["turn_count"] = 0
        # TODO: Collect metrics from phase 1 and persist for evaluation reporting


async def _handle_phrase_completion_phase(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs: Any) -> None:
    """Handle phrase completion interactions for phase 2 and collect metrics for evaluation"""
    pass


async def _handle_pronunciation_phase(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs: Any) -> None:
    """Handle pronunciation interactions for phase 3 and collect metrics for evaluation"""
    pass


async def _handle_final_phase(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs: Any) -> None:
    """Handle final interactions, conclude the evaluation and destroy the user_data evaluation context"""
    pass


PHASES_MAPPING = {
    "phase_1": _handle_voice_chat_phase,
    "phase_2": _handle_phrase_completion_phase,
    "phase_3": _handle_pronunciation_phase,
    "final_phase": _handle_final_phase,
}


async def evaluation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Orchestrates the evaluation flow,
    directing to the appropriate phase handler based on the user's current evaluation state.
    """
    # In evaluation mode, restrict interaction and prompt user to start the assessment
    if await block_until_start(update, context):
        return

    # Set initial evaluation state
    force_new_conversation = False
    if not context.user_data.get("evaluation"):
        force_new_conversation = True
        context.user_data["evaluation"] = {
            "phase": "phase_1",
            "turn_count": 0,
            "metrics": {},
        }

    current_phase = jsearch("evaluation.phase", context.user_data)
    handle_phase_func: Callable = PHASES_MAPPING.get(current_phase)
    if handle_phase_func:
        try:
            turn_count = jsearch("evaluation.turn_count", context.user_data)
            logger.info(f"Phase '{current_phase}' - Turn '{turn_count}' - User {update.message.from_user.id}")
            await handle_phase_func(update, context, force_new_conversation=force_new_conversation)
        except Exception as err:
            logger.error(f"Error handling evaluation phase. Details: {err}", exc_info=True)
            await update.message.reply_text("Ocorreu um erro durante a avaliação. Por favor, tente novamente.")
    else:
        logger.warning(f"Received message for unknown evaluation phase from user {update.message.from_user.id}")
        await update.message.reply_text(
            "Ocorreu um erro na avaliação. Por favor, reinicie o processo enviando '/start'."
        )

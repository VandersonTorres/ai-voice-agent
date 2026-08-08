from functools import partial

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import TELEGRAM_BOT_TOKEN

from . import on_shutdown, start
from .handlers import handle_what_agent_said, handle_what_user_said
from .handlers.text_handlers import text_handler
from .handlers.voice_handlers import voice_handler
from .handlers.evaluation_handlers import evaluation_handler


def run_telegram_bot(evaluation_mode: bool = False) -> None:
    """Main function to start the Telegram bot."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_shutdown(on_shutdown).build()

    start_handler = partial(start, evaluation_mode=evaluation_mode)

    # Commands Handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("whatYouSaid", handle_what_agent_said))
    app.add_handler(CommandHandler("whatISaid", handle_what_user_said))

    if evaluation_mode:
        app.add_handler(MessageHandler(filters.VOICE, evaluation_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, evaluation_handler))
    else:
        # Add Voice and Text handlers to free interaction with the bot
        app.add_handler(MessageHandler(filters.VOICE, voice_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # Start bot
    app.run_polling(timeout=30, bootstrap_retries=3)

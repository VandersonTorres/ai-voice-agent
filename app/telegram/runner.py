from functools import partial

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import TELEGRAM_BOT_TOKEN

from . import on_shutdown, start
from .handlers import (
    handle_text,
    handle_voice,
    handle_what_agent_said,
    handle_what_user_said,
    evaluation_text_handler,
    evaluation_voice_handler,
)


def run_telegram_bot(evaluation_mode: bool = False) -> None:
    """Main function to start the Telegram bot."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_shutdown(on_shutdown).build()

    start_handler = partial(start, evaluation_mode=evaluation_mode)

    # Commands Handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("whatYouSaid", handle_what_agent_said))
    app.add_handler(CommandHandler("whatISaid", handle_what_user_said))

    if evaluation_mode:
        # In evaluation mode, restrict interaction and prompt user to start the assessment
        app.add_handler(MessageHandler(filters.VOICE, evaluation_voice_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, evaluation_text_handler))
    else:
        # Add Voice and Text handlers to free interaction with the bot
        app.add_handler(MessageHandler(filters.VOICE, handle_voice))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Start bot
    app.run_polling(timeout=30, bootstrap_retries=3)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import TELEGRAM_BOT_TOKEN

from . import on_shutdown, start
from .handlers import handle_text, handle_voice, handle_what_agent_said, handle_what_user_said


def run_telegram_bot() -> None:
    """Main function to start the Telegram bot."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_shutdown(on_shutdown).build()

    # Commands Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("whatYouSaid", handle_what_agent_said))
    app.add_handler(CommandHandler("whatISaid", handle_what_user_said))

    # Voice message handler
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Text message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Start bot
    app.run_polling(timeout=30, bootstrap_retries=3)

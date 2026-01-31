from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import TELEGRAM_BOT_TOKEN

from . import on_shutdown, start
from .handlers import handle_text, handle_voice


def run_telegram_bot() -> None:
    """Main function to start the Telegram bot."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_shutdown(on_shutdown).build()

    # Commands Handlers
    app.add_handler(CommandHandler("start", start))

    # Voice message handler
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Text message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Start bot
    app.run_polling()

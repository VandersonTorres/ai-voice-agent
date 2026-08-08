import argparse

from app.logging import get_logger
from app.telegram.runner import run_telegram_bot

# from app.whatsapp.runner import run_wpp_bot

logger = get_logger(__name__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--use-telegram",
        action="store_true",
        help="Indicate the bot to use Telegram Integration",
    )
    parser.add_argument(
        "--use-whatsapp",
        action="store_true",
        help=("Indicate the bot to use WhatsApp Integration"),
    )
    parser.add_argument(
        "--evaluation-mode",
        action="store_true",
        help=("Indicate the bot to run in evaluation mode, conducting kind of an assessment with user"),
    )
    arguments = parser.parse_args()

    use_telegram = arguments.use_telegram
    use_whatsapp = arguments.use_whatsapp
    evaluation_mode = arguments.evaluation_mode
    if use_telegram:
        run_telegram_bot(evaluation_mode)
    elif not use_telegram and not use_whatsapp:
        logger.info("No integration specified. Starting Telegram bot by default.")
        run_telegram_bot(evaluation_mode)

    # elif use_whatsapp:
    #     TODO: Implement WhatsApp integration
    #     run_wpp_bot(evaluation_mode)

    else:
        logger.warning("Integration not supported")

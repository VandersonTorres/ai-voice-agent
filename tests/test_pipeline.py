import argparse
import asyncio
from pathlib import Path

from app.config import TEMP_DIR
from app.logging import get_logger
from app.pipelines.voice_pipeline import AudioPipeline
from app.pipelines.text_pipeline import TextPipeline

logger = get_logger(__name__)


def _args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-filename",
        type=str,
        help="Name of the input audio file (e.g., input.wav)",
    )
    parser.add_argument(
        "--input-text",
        type=str,
        help="A text input for the conversation (e.g., 'Hello, how are you today?')",
    )
    return parser.parse_args()


async def main():
    arguments = _args()
    if input_filename := arguments.input_filename:
        audio_pipeline = AudioPipeline()
        input_audio = Path(f"{TEMP_DIR}/{input_filename}")
        output_audio = Path(f"{TEMP_DIR}/output.mp3")  # Where to save the synthesized audio response
        result = await audio_pipeline.process_conversation(input_audio, output_audio)
    elif user_input_text := arguments.input_text:
        text_pipeline = TextPipeline()
        result = await text_pipeline.process_conversation(user_input_text)
    else:
        logger.error("No input provided. Please provide either --input-filename or --input-text.")
        return

    logger.info("\n=== RESULT ===")
    for k, v in result.items():
        logger.info(f"{k}: {v}")

    if input_filename:
        await audio_pipeline.llm.close()
    elif user_input_text:
        await text_pipeline.llm.close()


if __name__ == "__main__":
    asyncio.run(main())

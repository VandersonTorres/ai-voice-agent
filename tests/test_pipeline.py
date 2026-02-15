import argparse
import asyncio
from pathlib import Path

from app.config import TEMP_DIR
from app.logging import get_logger
from app.pipelines.voice_pipeline import AudioPipeline
from app.pipelines.text_pipeline import TextPipeline

logger = get_logger()


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
    audio_pipeline = AudioPipeline()
    text_pipeline = TextPipeline()

    args = _args()
    if filename := args.input_filename:
        input_audio = Path(f"{TEMP_DIR}/{filename}")
        output_audio = Path(f"{TEMP_DIR}/output.mp3")  # Where to save the synthesized audio response
        result = await audio_pipeline.process_conversation(input_audio, output_audio)
    elif user_input_text := args.input_text:
        result = await text_pipeline.process_conversation(user_input_text)
    else:
        logger.error("No input provided. Please provide either --input-filename or --input-text.")
        return

    logger.info("\n=== RESULT ===")
    for k, v in result.items():
        logger.info(f"{k}: {v}")

    await audio_pipeline.llm.close()
    await text_pipeline.llm.close()


if __name__ == "__main__":
    asyncio.run(main())

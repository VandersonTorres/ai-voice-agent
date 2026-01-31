import asyncio
from pathlib import Path
from app.pipelines.voice_pipeline import AudioPipeline

# from app.pipelines.text_pipeline import TextPipeline
from app.config import TEMP_DIR


async def main():
    audio_pipeline = AudioPipeline()
    # text_pipeline = TextPipeline()

    # user_input_text = "Hello, how are you today?"
    input_audio = Path(f"{TEMP_DIR}/input.wav")
    output_audio = Path(f"{TEMP_DIR}/output.mp3")

    result = await audio_pipeline.process_conversation(input_audio, output_audio)
    # result = await text_pipeline.process_conversation(user_input_text)

    print("\n=== RESULT ===")
    for k, v in result.items():
        print(f"{k}: {v}")

    await audio_pipeline.llm.close()
    # await text_pipeline.llm.close()


if __name__ == "__main__":
    asyncio.run(main())

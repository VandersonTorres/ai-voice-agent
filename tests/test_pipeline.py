import asyncio
from pathlib import Path
from app.pipelines.voice_pipeline import AudioConversationPipeline
from app.config import TEMP_DIR

async def main():
    pipeline = AudioConversationPipeline()

    input_audio = Path(f"{TEMP_DIR}/input.wav")
    output_audio = Path(f"{TEMP_DIR}/output.mp3")

    result = await pipeline.process_audio_conversation(input_audio, output_audio)

    print("\n=== RESULT ===")
    for k, v in result.items():
        print(f"{k}: {v}")

    await pipeline.llm.close()


if __name__ == "__main__":
    asyncio.run(main())

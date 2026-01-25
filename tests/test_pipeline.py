import asyncio
from pathlib import Path
from app.pipelines.voice_pipeline import VoicePipeline


async def main():
    pipeline = VoicePipeline()

    input_audio = Path("data/temp_audio/input.wav")
    output_audio = Path("data/temp_audio/output.mp3")

    result = await pipeline.process(input_audio, output_audio)

    print("\n=== RESULT ===")
    for k, v in result.items():
        print(f"{k}: {v}")

    await pipeline.llm.close()


if __name__ == "__main__":
    asyncio.run(main())

from pathlib import Path
from app.pipelines.voice_pipeline import VoicePipeline


if __name__ == "__main__":
    pipeline = VoicePipeline()

    input_audio = Path("data/temp_audio/input.wav")
    output_audio = Path("data/temp_audio/output.mp3")

    result = pipeline.process(input_audio, output_audio)

    print("\n=== RESULTADO ===")
    for k, v in result.items():
        print(f"{k}: {v}")

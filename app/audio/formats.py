import subprocess
from pathlib import Path


def ogg_to_wav(
    input_path: Path,
    output_path: Path,
    sample_rate: int = 16000,
):
    """Convert an audio file from OGG format to WAV format

    This function uses FFmpeg to convert an OGG/Opus audio file into
    a mono WAV file with a fixed sample rate, optimized for speech
    recognition models such as Whisper.

    :input_path: Path to the input OGG audio file
    :output_path: Path where the converted WAV file will be saved
    :sample_rate: Target audio sample rate in Hz (default: 16000)
    :raises subprocess.CalledProcessError: If the FFmpeg conversion fails
    """
    command = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-ac", "1",  # mono
        "-ar", str(sample_rate),  # target sample rate
        str(output_path),
    ]

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    # Remove the original OGG file after successful conversion
    input_path.unlink()

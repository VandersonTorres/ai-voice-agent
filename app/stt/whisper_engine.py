import whisper
from typing import Dict

from app.config import WHISPER_MODEL
from app.logging import get_logger


class WhisperEngine:
    """Speech-to-Text engine using OpenAI Whisper model"""

    def __init__(self) -> None:
        """Initialize the Whisper STT engine"""
        self.model = whisper.load_model(WHISPER_MODEL)
        self.logger = get_logger(self.__class__.__name__)

    def transcribe(self, audio_path: str) -> Dict[str, str]:
        """
        Transcribe an audio to text with high literal fidelity.

        :param audio_path: Path to the audio file
        :return: Dict containing transcribed text and detected language
        """
        self.logger.info("[STT] Transcribing audio input...")

        result = self.model.transcribe(
            audio_path,
            task="transcribe",
            temperature=0.0,  # Less creative
            beam_size=1,  # Less reinterpretation
            best_of=1,  # Avoid choosing prettiest phrases
            condition_on_previous_text=False,  # Don't complete sentences
            word_timestamps=True,  # More literalness
            verbose=False,
        )

        text = result.get("text", "").strip()
        detected_language = result.get("language", "unknown")

        return {
            "text": text,
            "language": detected_language,
        }

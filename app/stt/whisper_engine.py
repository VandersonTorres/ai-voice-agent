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
        """Transcribe an audio to text

        :audio_path: The path to the audio file.
        :returns: Dict containing the transcribed text and language detected
        """
        self.logger.info("[STT] Transcribing audio input...")
        result = self.model.transcribe(audio_path)
        return {"text": result["text"].strip(), "language": result.get("language", "unknown")}

from typing import Dict

from openai import OpenAI

from app.config import WHISPER_MODEL, IS_PRODUCTION
from app.logging import get_logger


# Development Environment
class WhisperEngine:
    """Speech-to-Text engine using OpenAI Whisper model"""

    def __init__(self) -> None:
        """Initialize the Whisper STT engine"""
        # Imported lazily so the production path (OpenAI API) does not require
        # torch/whisper to be installed.
        import whisper  # type: ignore

        self.model = whisper.load_model(WHISPER_MODEL)
        self.logger = get_logger(self.__class__.__name__)

    def transcribe(self, audio_path: str) -> Dict[str, str]:
        """Transcribe an audio to text with high literal fidelity.

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


# Production Environment
class OpenAIEngine:
    """Speech-to-Text engine using OpenAI's audio transcription API"""

    def __init__(self):
        """Initialize the OpenAI STT engine"""
        self.client = OpenAI()
        self.logger = get_logger(self.__class__.__name__)

    def detect_language(self, text: str) -> str:
        """Detect the language of the given text using OpenAI's language detection capabilities."""
        response = self.client.responses.create(
            model="gpt-4o-mini",
            input=(
                "Detect the language of this text. "
                "Answer with only the language abbreviation according to the universal convention "
                f"(e.g., 'en', 'pt', 'fr'):\n\n{text}"
            ),
        )
        return response.output_text.strip()

    def transcribe(self, audio_path: str) -> Dict[str, str]:
        """Transcribe an audio file to text using OpenAI's audio transcription API.

        :param audio_path: Path to the audio file
        :return: Dict containing transcribed text and detected language
        """
        self.logger.info("[STT] Transcribing audio input...")

        with open(audio_path, "rb") as f:
            transcript = self.client.audio.transcriptions.create(model="gpt-4o-mini-transcribe", file=f)

        text = transcript.text.strip()
        lang = self.detect_language(text)
        return {
            "text": text,
            "language": lang,
        }


class STTEngineFactory:
    """Factory class to create instances of STT engines"""

    @staticmethod
    def create_engine() -> WhisperEngine | OpenAIEngine:
        """Create an instance of the specified STT engine type

        :return: An instance of the requested STT engine
        """
        if IS_PRODUCTION:
            return OpenAIEngine()

        return WhisperEngine()

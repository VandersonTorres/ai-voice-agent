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


# Evaluation Environment (ultra-literal transcription settings)
class LiteralWhisperEngine(WhisperEngine):
    """Whisper engine optimized for ultra-literal transcription (evaluation mode)"""

    def transcribe(self, audio_path: str, probability_threshold: float = 0.4) -> Dict[str, str]:
        """Transcribe audio with a focus on literal accuracy.

        :param audio_path: Path to the audio file
        :param probability_threshold: Threshold below which words are flagged as low confidence
        :return: Dict containing transcribed text, detected language, and low confidence words
        """
        self.logger.info("[STT] Transcribing audio input (LITERAL MODE)...")

        result = self.model.transcribe(
            audio_path,
            task="transcribe",
            temperature=0.0,
            beam_size=1,
            best_of=1,
            condition_on_previous_text=False,
            no_speech_threshold=0.3,
            logprob_threshold=-2.0,
            compression_ratio_threshold=1.4,
            word_timestamps=True,
            verbose=False,
        )

        text = result.get("text", "").strip()
        detected_language = result.get("language", "unknown")
        low_confidence_words = []
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                probability = word_info.get("probability")
                if probability is None:
                    self.logger.warning(f"Word info missing 'probability': {word_info}")
                    continue

                probability = float(probability)
                if probability < probability_threshold:
                    low_confidence_words.append(word_info.get("word", ""))

        return {"text": text, "language": detected_language, "low_confidence_words": low_confidence_words}


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
    def create_engine(evaluation_mode: bool = False) -> WhisperEngine | LiteralWhisperEngine | OpenAIEngine:
        """Create an instance of the specified STT engine type

        :param evaluation_mode: If True, creates a LiteralWhisperEngine optimized for evaluation;
            otherwise, creates a standard WhisperEngine or OpenAIEngine based on environment
        :return: An instance of the requested STT engine
        """
        engine = WhisperEngine()
        if IS_PRODUCTION:
            engine = OpenAIEngine()

        if evaluation_mode:
            engine = LiteralWhisperEngine()

        return engine

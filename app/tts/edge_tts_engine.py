import edge_tts
from pathlib import Path

from app.logging import get_logger
from app.tts.voices import DEFAULT_VOICE, VOICE_BY_LANGUAGE, RATE_BY_LANGUAGE


class EdgeTTSEngine:
    """Text-to-Speech engine using Edge TTS"""

    def __init__(self, language: str) -> None:
        """Initialize the Edge TTS engine

        :language: The language identifier to be used for speech synthesis (e.g., 'en', 'es', 'de', 'zh', 'pt').
        """
        self.language = language.lower()
        self.logger = get_logger(self.__class__.__name__)

    def _get_voice_for_language(self) -> str:
        """Determine the appropriate Edge TTS voice based on the language, with fallbacks for unsupported languages."""
        supported_languages = set(VOICE_BY_LANGUAGE.keys())
        if self.language in supported_languages:
            voice = VOICE_BY_LANGUAGE.get(self.language)
            self.logger.info(f"Selected voice '{voice}' for language '{self.language}'")
        elif self.language.startswith(("nl", "sv", "no")):
            voice = "de-DE-KatjaNeural"
            self.logger.warning(f"Language '{self.language}' not supported. Using voice '{voice}' as fallback")
        else:
            voice = DEFAULT_VOICE
            self.logger.warning(f"Language '{self.language}' not supported. Using fallback voice {DEFAULT_VOICE} ")

        return voice

    async def _synthesize_speech_from_text(self, text: str, output_path: Path) -> Path:
        """Asynchronously synthesize speech from text using Edge TTS

        :text: The text to be converted into speech
        :output_path: The path where the generated audio file will be saved
        :returns: The output audio path after sinthesizing
        """
        rate = RATE_BY_LANGUAGE.get(self.language, "+0%")
        voice = self._get_voice_for_language()
        self.logger.info(f"[TTS] Synthesizing speech to {output_path}")
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch="+12Hz",
        )
        await communicate.save(output_path)
        return output_path

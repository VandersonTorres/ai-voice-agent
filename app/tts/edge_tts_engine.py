import edge_tts
from pathlib import Path

from app.logging import get_logger


class EdgeTTSEngine:
    """Text-to-Speech engine using Edge TTS"""

    def __init__(self, voice: str) -> None:
        """Initialize the Edge TTS engine

        :voice: The voice identifier to be used for speech synthesis
        """
        self.voice = voice
        self.logger = get_logger(self.__class__.__name__)

    async def _synthesize_async(self, text: str, output_path: Path) -> None:
        """Asynchronously synthesize speech from text using Edge TTS

        :text: The text to be converted into speech
        :output_path: The path where the generated audio file will be saved
        """
        self.logger.info(f"[TTS] Synthesizing speech to {output_path} using voice '{self.voice}'")
        communicate = edge_tts.Communicate(text=text, voice=self.voice)
        await communicate.save(output_path)

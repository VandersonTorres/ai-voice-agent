import json
from pathlib import Path

from app.audio.formats import ogg_to_wav
from app.llm.prompts import SYSTEM_PROMPT
from app.llm.conversation_memory import ConversationMemory
from app.llm.conversation_state import ConversationState
from app.llm.conversation_topic_detector import TopicDetector
from app.llm.conversation_state_summarizer import ConversationStateSummarizer
from app.llm.ollama_client import OllamaClient
from app.logging import get_logger
from app.stt.whisper_engine import WhisperEngine
from app.tts.edge_tts_engine import EdgeTTSEngine
from app.tts.voices import DEFAULT_VOICE, VOICE_BY_LANGUAGE
from app.utils import run_in_thread


class VoicePipelineAsync:
    """
    This pipeline orchestrates the full audio-to-audio flow:
    speech-to-text (Whisper), text generation (Ollama),
    and text-to-speech (Edge TTS).
    """

    def __init__(self) -> None:
        """Initialize the voice processing pipeline"""
        self.stt = WhisperEngine()
        self.llm = OllamaClient()

        self.memory = ConversationMemory(max_turns=5)
        self.state = ConversationState()
        self.topic_detector = TopicDetector()
        self.summarizer = ConversationStateSummarizer(llm=self.llm)

        self.logger = get_logger(self.__class__.__name__)

    async def process(self, input_audio_path: Path, output_audio_path: Path):
        """Process an input audio file and generate a spoken response

        The method executes the following steps:
        1. Transcribes the input audio using Whisper
        2. Generates a textual response using the language model
        3. Converts the response text into speech using Edge TTS

        :input_audio_path: Path to the input audio file (WAV format expected)
        :output_audio_path: Path where the generated output audio will be saved
        :returns: A dictionary containing the transcription, response,
            detected language, and output audio path
        """
        # 1. STT (thread) Ensure WAV format)
        if input_audio_path.suffix.lower() != ".wav":
            wav_path = input_audio_path.with_suffix(".wav")
            await run_in_thread(ogg_to_wav, input_audio_path, wav_path)
        else:
            wav_path = input_audio_path

        stt_result = await run_in_thread(self.stt.transcribe, str(wav_path))
        language = stt_result["language"]
        user_text = stt_result["text"]

        self.logger.info(f"[STT] Received prompt:\n\t({language}) {user_text}")

        # 2. Topic detection
        if self.topic_detector.is_new_topic(self.state.summary, user_text):
            self.logger.info("Topic change detected. Resetting conversation state.")
            self.state.clear()
            self.memory.clear()

        # 3. Prompt
        context_block = ""
        if not self.state.is_empty():
            context_block = f"""
                Conversation context:
                Topic: {self.state.topic}
                Summary: {self.state.summary}
                User tone: {self.state.tone}
                """

        if self.state.language and language != self.state.language:
            # If user changes language, avoids to mix multilanguages contexts
            self.state.clear()
            self.memory.clear()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + context_block},
            *self.memory.get_messages(),
            {"role": "user", "content": user_text},
        ]

        # 4. LLM (async)
        for msg in messages:
            self.logger.debug(f"\nEnqueued message: {msg}")

        answer = await self.llm.chat(messages)
        self.logger.info(f"[LLM] Response:\n\t{answer}")
        self.memory.add_user_message(user_text)
        self.memory.add_assistant_message(answer)

        # 5. Update state (async)
        raw_state = await self.summarizer.update_state(
            previous_summary=self.state.summary,
            user_text=user_text,
            assistant_text=answer,
            language=language,
        )

        try:
            parsed = json.loads(raw_state)
        except json.JSONDecodeError:
            parsed = {}

        self.state.topic = parsed.get("topic")
        self.state.summary = parsed.get("summary")
        self.state.tone = parsed.get("tone")
        self.state.language = language

        # 6. TTS (async)
        supported_languages = set(VOICE_BY_LANGUAGE.keys())
        if language not in supported_languages:
            voice = DEFAULT_VOICE
            self.logger.warning(f"Language {language} not supported. Using fallback voice {DEFAULT_VOICE} ")
        else:
            voice = VOICE_BY_LANGUAGE.get(language)

        tts = EdgeTTSEngine(voice=voice)
        await tts._synthesize_async(answer, output_audio_path)

        return {
            "user_text": user_text,
            "answer_text": answer,
            "language": language,
            "audio_path": output_audio_path,
        }

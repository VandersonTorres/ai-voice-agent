from pathlib import Path
from typing import Any

from app.audio.formats import to_wav
from app.llm.conversation_memory import ConversationReminder
from app.pipelines import BaseConversationPipeline
from app.stt.stt_engine import STTEngineFactory
from app.tts.edge_tts_engine import EdgeTTSEngine
from app.tts.voices import DEFAULT_VOICE, VOICE_BY_LANGUAGE
from app.utils import run_in_thread


class AudioPipeline(BaseConversationPipeline):
    """
    This pipeline orchestrates the full audio-to-audio flow:
    speech-to-text (Whisper),
    and text-to-speech (Edge TTS).
    """

    def __init__(self) -> None:
        super().__init__()
        self.stt = STTEngineFactory.create_engine()

    async def transcribe_user_audio(self, audio_path: Path) -> dict[str, Any]:
        """Run the user audio through the Speech-To-Text pipeline, ensuring WAV format.

        :audio_path: Path to the input audio file (sent by the user)
        :returns: Dict containing both language, transcribed text and new user_input_audio_path.
        """
        if audio_path.suffix.lower() != ".wav":
            wav_path = audio_path.with_suffix(".wav")
            await run_in_thread(to_wav, audio_path, wav_path)
        else:
            wav_path = audio_path

        stt_result = await run_in_thread(self.stt.transcribe, str(wav_path))
        language = stt_result["language"]
        user_input_text = stt_result["text"]
        return {"language": language, "user_input_text": user_input_text, "user_input_audio_path": wav_path}

    async def synthesize_audio_output(self, language: str, model_output_text: str, output_audio_path: Path) -> Path:
        """Synthesize the model output text into speech audio using Edge TTS

        :language: Language used for synthesis
        :model_output_text: Text to be synthesized
        :output_audio_path: Path to save the synthesized audio
        :returns: Path to the synthesized audio file
        """
        supported_languages = set(VOICE_BY_LANGUAGE.keys())
        if language not in supported_languages:
            voice = DEFAULT_VOICE
            self.logger.warning(f"Language {language} not supported. Using fallback voice {DEFAULT_VOICE} ")
        else:
            voice = VOICE_BY_LANGUAGE.get(language)

        tts = EdgeTTSEngine(voice=voice)
        output_path = await tts._synthesize_speech_from_text(model_output_text, output_audio_path)
        return output_path

    async def process_conversation(
        self,
        user_input_audio_path: Path,
        output_audio_path: Path,
        chat_memory: ConversationReminder,
        user_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Orchestrates the full audio-to-audio conversation flow.

        The method executes the following steps:
        1. Transcribes the input audio to text using Whisper (STT)
        2. Detects if the topic has changed and resets context if needed
        3. Prepares prompts including conversation history for the LLM
        4. Sends prompts to the LLM and retrieves the generated response
        5. Updates the conversation context and state
        6. Synthesizes the LLM response into speech audio using Edge TTS

        :user_input_audio_path: Path to the input audio file (WAV format expected)
        :output_audio_path: Path where the generated output audio will be saved
        :chat_memory: ConversationReminder instance containing the conversation history
        :user_profile: Optional dictionary containing user profile information (e.g., name, preferences)
        :returns: A dictionary containing:
            language, user_input_text, user_input_audio_path,
            model_output_text and synthesized_audio_path, parsed_profile
        """
        # User input preparing (STT)
        stt_result = await self.transcribe_user_audio(user_input_audio_path)
        language = stt_result["language"]
        user_input_text = stt_result["user_input_text"]
        self.logger.info(f"[STT] Received prompt:\n\t({language}) {user_input_text}")

        # Topic detection
        if self.topic_detector.is_new_topic(self.state.summary, user_input_text):
            self.logger.info("Topic change detected. Resetting conversation state.")
            self.state.clear()
            chat_memory.clear()

        # Prompt construction
        prompts = self.prepare_prompts_to_llm(language, user_input_text, chat_memory, user_profile)
        for prompt in prompts:
            self.logger.debug(f"\nEnqueued prompt: {prompt}")

        # LLM output preparing
        model_output_text = await self.llm.chat(prompts)
        self.logger.info(f"[LLM] Response:\n\t{model_output_text}")
        chat_memory.add_user_message(user_input_text)
        chat_memory.add_assistant_message(model_output_text)

        # Conversation context update
        await self.update_conversation_context(language, user_input_text, model_output_text)
        self.logger.info("Conversation context was updated succesfully.")

        parsed_profile = await self.update_user_profile(chat_memory, user_profile)
        if parsed_profile:
            self.logger.info(f"User profile was updated successfully:\n\t{parsed_profile}")

        # Output voice audio preparing (TTS)
        synthesized_audio_path = await self.synthesize_audio_output(language, model_output_text, output_audio_path)

        return {
            "language": language,
            "user_input_text": user_input_text,
            "user_input_audio_path": stt_result["user_input_audio_path"],
            "model_output_text": model_output_text,
            "synthesized_audio_path": synthesized_audio_path,
            "parsed_profile": parsed_profile,
        }

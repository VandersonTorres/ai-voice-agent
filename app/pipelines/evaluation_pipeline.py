from pathlib import Path
from typing import Any

from app.llm.conversation_memory import ConversationReminder
from app.llm.prompts import EVALUATION_MODE_SYSTEM_PROMPT
from app.pipelines.voice_pipeline import AudioPipeline
from app.stt.stt_engine import STTEngineFactory
from app.utils import run_in_thread


class EvaluationAudioPipeline(AudioPipeline):
    """
    This pipeline is responsible for evaluating the user's language proficiency
    through audio input and providing feedback.
    """

    def __init__(self) -> None:
        super().__init__()
        self.literal_stt = STTEngineFactory.create_engine(evaluation_mode=True)

    async def transcribe_user_audio(self, audio_path: Path) -> dict[str, Any]:
        stt_result = await super().transcribe_user_audio(audio_path)

        wav_path = audio_path.with_suffix(".wav")
        literal_stt_result = await run_in_thread(self.literal_stt.transcribe, str(wav_path))
        user_literal_input_text = literal_stt_result["text"]
        self.logger.info(
            f"[STT] Literal transcription result:\n\t{user_literal_input_text}\n\n"
            f"[STT] Interpretation result: \n\t{stt_result['user_input_text']}"
        )
        stt_result.update(
            {
                "user_literal_input_text": user_literal_input_text,
                # "low_confidence_words": literal_stt_result.get("low_confidence_words", [])
            }
        )
        return stt_result

    def prepare_prompts_to_llm(
        self,
        user_input_text: str,
        user_literal_text: str,
        chat_memory: ConversationReminder,
        user_profile: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        prompts = [{"role": "system", "content": EVALUATION_MODE_SYSTEM_PROMPT}]

        context_block = ""
        if user_profile:
            context_block = (
                "User General Profile:\n"
                f"Name: {user_profile.get('name', '')}\n"
                f"Preferred languages: {user_profile.get('preferred_languages', '')}\n"
                f"Interests: {user_profile.get('interests', '')}\n"
                f"Conversation style: {user_profile.get('conversation_style', '')}\n"
            )

        if not self.state.is_empty():
            context_block += (
                "Current Conversation Context:\n"
                f"Topic: {self.state.topic}\n"
                f"Summary: {self.state.summary}\n"
                f"User tone: {self.state.tone}\n"
            )
        if context_block:
            prompts.append(
                {
                    "role": "system",
                    "content": f"- 'Conversation context' (use as guidance, not strict rules):\n{context_block}",
                }
            )

        prompts.extend(
            [
                *chat_memory.get_messages(),
                {"role": "user", "content": f"Literal: {user_literal_text}"},
                {"role": "system", "content": f"Interpretation of literal input: {user_input_text}"},
            ]
        )
        return prompts

    async def process_conversation(
        self,
        user_input_audio_path: Path,
        output_audio_path: Path,
        chat_memory: ConversationReminder,
        user_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # User input preparing (STT)
        stt_result = await self.transcribe_user_audio(user_input_audio_path)
        language = stt_result["language"]
        user_input_text = stt_result["user_input_text"]
        user_literal_text = stt_result["user_literal_input_text"]
        # low_confidence_words = stt_result.get("low_confidence_words", [])

        self.logger.info(f"[STT] Received prompt:\n\t({language}) {user_literal_text}")

        # Prompt construction
        prompts = self.prepare_prompts_to_llm(user_literal_text, user_literal_text, chat_memory, user_profile)
        for prompt in prompts:
            self.logger.debug(f"\nEnqueued prompt: {prompt}")

        # LLM output preparing
        model_output_text = await self.llm.chat(prompts)
        self.logger.info(f"[LLM] Response:\n\t{model_output_text}")
        chat_memory.add_user_message(user_literal_text)
        chat_memory.add_assistant_message(model_output_text)

        # Conversation context update
        await self.update_conversation_context(language, user_literal_text, model_output_text)
        self.logger.info("Conversation context was updated succesfully.")

        parsed_profile = await self.update_user_profile(chat_memory, user_profile)
        if parsed_profile:
            self.logger.info(f"User profile was updated successfully:\n\t{parsed_profile}")

        # Output voice audio preparing (TTS)
        synthesized_audio_path = await self.synthesize_audio_output(model_output_text, output_audio_path)

        return {
            "language": language,
            "user_input_text": user_input_text,
            "user_literal_text": user_literal_text,
            "user_input_audio_path": stt_result["user_input_audio_path"],
            "model_output_text": model_output_text,
            "synthesized_audio_path": synthesized_audio_path,
            "parsed_profile": parsed_profile,
        }

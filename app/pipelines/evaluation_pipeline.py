# TODO: Implement the evaluation pipelines (voice and text)
from app.pipelines import BaseConversationPipeline


class EvaluationAudioPipeline(BaseConversationPipeline):
    """
    This pipeline orchestrates the full audio-to-audio flow:
    speech-to-text (Whisper),
    and text-to-speech (Edge TTS).
    """

    def __init__(self) -> None:
        super().__init__()
        # TODO: self.stt should be a literal transcriptor without any prompt engineering or conversation context,
        # to ensure the most accurate transcription possible for evaluation purposes.
        # We need create a new STT engine class that inherits from the existing one
        # but overrides the transcribe method to bypass any prompt engineering.

    def prepare_prompts_to_llm(self, user_input_text, chat_memory, user_profile=None):
        # TODO: Should prepare the prompts with the EVALUATION_MODE_SYSTEM_PROMPT,
        # that instructs the LLM to evaluate the user's language proficiency based on the input text
        # and provide feedback and suggestions for improvement.
        return super().prepare_prompts_to_llm(user_input_text, chat_memory, user_profile)

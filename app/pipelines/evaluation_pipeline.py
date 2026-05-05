from app.llm.prompts import EVALUATION_MODE_SYSTEM_PROMPT
from app.pipelines import BaseConversationPipeline
from app.stt.stt_engine import STTEngineFactory


class EvaluationAudioPipeline(BaseConversationPipeline):
    """
    This pipeline orchestrates the full audio-to-audio flow:
    speech-to-text (Whisper),
    and text-to-speech (Edge TTS).
    """

    def __init__(self) -> None:
        super().__init__()
        self.stt = STTEngineFactory.create_engine(evaluation_mode=True)

    def prepare_prompts_to_llm(self, user_input_text, chat_memory, user_profile=None):
        # TODO: Should prepare the prompts with the EVALUATION_MODE_SYSTEM_PROMPT,
        # that instructs the LLM to evaluate the user's language proficiency based on the input text
        # and provide feedback and suggestions for improvement.
        prompts = [{"role": "system", "content": EVALUATION_MODE_SYSTEM_PROMPT}]
        prompts.extend(
            [
                *chat_memory.get_messages(),
                {"role": "user", "content": user_input_text},
            ]
        )
        return prompts

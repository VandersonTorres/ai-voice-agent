from app.llm.ollama_client import OllamaClient
from app.logging import get_logger


class ConversationStateSummarizer:
    """Uses the LLM to incrementally summarize the conversation state."""

    def __init__(self, llm: OllamaClient) -> None:
        self.llm = llm
        self.logger = get_logger(self.__class__.__name__)

    async def update_state(
        self,
        previous_summary: str | None,
        user_text: str,
        assistant_text: str,
        language: str,
    ) -> dict:
        """
        Generate an updated summary, topic and tone based on
        the latest interaction.
        """

        prompt = (
            f"""
            You are summarizing a spoken conversation.

            Previous summary:
            {previous_summary or "None"}

            User said:
            {user_text}

            Assistant replied:
            {assistant_text}

            Return a concise JSON with:
            - topic
            - summary (1 or 2 sentences max)
            - tone (e.g. curious, neutral, serious, relaxed)

            Respond ONLY with valid JSON.
            Language: {language}
            """
        )

        self.logger.info("[LLM] Updating context state...")
        response = await self.llm.chat(
            [{"role": "user", "content": prompt}]
        )

        return response

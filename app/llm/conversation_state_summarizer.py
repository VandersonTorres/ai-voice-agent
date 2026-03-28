import json
from typing import Any

from app.config import MAX_CONVERSATION_TURNS
from app.llm.llm_api_client import LLMClient
from app.logging import get_logger


class ConversationStateSummarizer:
    """Uses the LLM to incrementally summarize the conversation state."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm
        self.logger = get_logger(self.__class__.__name__)

    async def get_updated_state(
        self,
        previous_summary: str | None,
        user_text: str,
        assistant_text: str,
        language: str,
    ) -> dict[str, Any]:
        """
        Generate an updated summary, topic and tone based on
        the latest interaction.
        """

        prompt = f"""
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

        self.logger.info("[LLM] Updating context state...")
        response = await self.llm.chat([{"role": "user", "content": prompt}])

        return response

    async def get_updated_user_profile(
        self, previous_user_profile: dict[str, Any] | None, last_messages: list[dict[str, str]]
    ) -> dict[str, Any]:
        update_profile_prompt = f"""
            You are summarizing a user profile.

            Previous profile summary:
            {previous_user_profile or "None"}

            Previous {MAX_CONVERSATION_TURNS} conversation turns:
            {json.dumps(last_messages, ensure_ascii=False, indent=2)}

            Return a concise JSON with:
            - (str) user name (if mentioned, otherwise return null)
            - (list) preferred_languages (spoken languages or mentioned languages in the conversation)
            - (list) interests
            - (str) conversation_style (e.g. formal, casual, concise, detailed, humorous, etc.)

            Respond ONLY with valid JSON.
            """

        self.logger.info("[LLM] Updating context state...")
        profile_response = await self.llm.chat([{"role": "user", "content": update_profile_prompt}])
        return profile_response

from difflib import SequenceMatcher

from app.llm.llm_api_client import LLMClient


class TopicDetector:
    """
    Detects whether the user changed the conversation topic
    using semantic similarity heuristics.
    """

    def __init__(self, similarity_threshold: float = 0.35) -> None:
        self.similarity_threshold = similarity_threshold

    async def is_requesting_audio_response(self, user_input_text: str, llm_client: LLMClient) -> bool:
        """Detects if the user is requesting an audio response.

        :user_input_text: The text input from the user
        :returns: True if an audio response is requested, False otherwise
        """
        # Implement your detection logic here
        prompt = (
            "Determine if the user is requesting an audio response based on the following input:\n"
            f"{user_input_text}\n\n"
            "You should return a text-based boolean value: 'True' or 'False'. "
            "Return 'True' if an audio response is requested, and 'False' otherwise."
        )
        response = await llm_client.chat([{"role": "user", "content": prompt}])
        return response.strip().lower() == "true"

    def is_new_topic(self, previous_summary: str | None, new_text: str) -> bool:
        """
        Determine if the new user input represents a topic change.

        :param previous_summary: Current conversation summary
        :param new_text: New user utterance
        """
        if not previous_summary:
            return False

        similarity = SequenceMatcher(
            None,
            previous_summary.lower(),
            new_text.lower(),
        ).ratio()

        return similarity < self.similarity_threshold

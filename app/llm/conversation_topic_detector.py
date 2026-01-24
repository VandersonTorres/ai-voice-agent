from difflib import SequenceMatcher


class TopicDetector:
    """
    Detects whether the user changed the conversation topic
    using semantic similarity heuristics.
    """

    def __init__(self, similarity_threshold: float = 0.35) -> None:
        self.similarity_threshold = similarity_threshold

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

from typing import Optional


class ConversationState:
    """
    Stores a compact semantic state of the conversation to maintain
    continuity without keeping full message history.
    """

    def __init__(self):
        self.topic: Optional[str] = None
        self.summary: Optional[str] = None
        self.tone: Optional[str] = None
        self.language: Optional[str] = None

    def clear(self) -> None:
        """Reset the conversation state"""
        self.topic = None
        self.summary = None
        self.tone = None
        self.language = None

    def is_empty(self) -> bool:
        """Check whether the conversation state is empty"""
        return not any([self.topic, self.summary, self.tone])

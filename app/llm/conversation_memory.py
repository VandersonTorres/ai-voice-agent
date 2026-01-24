from collections import deque
from typing import Deque, Dict, List


class ConversationMemory:
    """
    Manages a short-term conversational memory to maintain context
    across multiple user interactions.
    """

    def __init__(self, max_turns: int = 5):
        """
        Initialize the conversation memory.

        :param max_turns: Maximum number of user/assistant turns to keep
        """
        self.max_turns = max_turns
        self.history: Deque[Dict[str, str]] = deque(maxlen=max_turns * 2)

    def add_user_message(self, text: str) -> None:
        """Add a user message to the memory"""
        self.history.append({"role": "user", "content": text})

    def add_assistant_message(self, text: str) -> None:
        """Add an assistant message to the memory"""
        self.history.append({"role": "assistant", "content": text})

    def get_messages(self) -> List[Dict[str, str]]:
        """Return the conversation history formatted for the LLM."""
        return list(self.history)

    def clear(self) -> None:
        """Clear the conversation memory"""
        self.history.clear()

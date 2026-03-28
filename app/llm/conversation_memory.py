from collections import deque
from typing import Deque, Dict, List

from app.config import MAX_CONVERSATION_TURNS


class ConversationReminder:
    """Class to manage conversation history for a single chat session.

    It stores a limited number of recent user and assistant messages to provide context for the LLM.
    """

    def __init__(self, max_turns: int = MAX_CONVERSATION_TURNS) -> None:
        """
        Initialize the conversation memory.

        :param max_turns: Maximum number of user/assistant turns to keep
        """
        self.max_turns = max_turns
        self.history: Deque[Dict[str, str]] = deque(maxlen=max_turns)

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


class RapidMemoryManager:
    """
    Singleton store for ConversationReminder instances per chat_id.
    """

    _store: dict[str, ConversationReminder] = {}

    @classmethod
    def get_memory(cls, chat_id: str) -> ConversationReminder:
        if chat_id not in cls._store:
            cls._store[chat_id] = ConversationReminder()

        return cls._store[chat_id]

    @classmethod
    def clear_memory(cls, chat_id: str) -> None:
        if chat_id in cls._store:
            cls._store[chat_id].clear()

    @classmethod
    def reset_all(cls) -> None:
        cls._store.clear()

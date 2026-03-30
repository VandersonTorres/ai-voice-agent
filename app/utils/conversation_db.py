import sqlite3
import json
from datetime import datetime, timezone
from typing import Any, List, Dict, Optional

from pathlib import Path

from app.config import DB_PATH


class ConversationDB:
    """Simple SQLite-based database for storing conversations and user profiles."""

    max_entries_per_chat = 30  # Max number of messages to store per chat session

    def __init__(self, db_path: Path = DB_PATH) -> None:
        """Initialize the database connection and create tables if they don't exist."""
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self) -> None:
        """Create the necessary tables for conversations and profiles if they don't already exist.

        - Conversations table: Stores the last messages for each chat_id.
        - Profile table: Stores a summary of the user profile and preferences.
        """
        cur = self.conn.cursor()

        # Create conversations table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                chat_id TEXT PRIMARY KEY,
                messages TEXT,
                profile TEXT,
                last_message_ts TEXT
            )
            """
        )
        self.conn.commit()

    def get_conversation(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the conversation history for a given chat_id.

        :chat_id: The unique identifier for the chat session
        :returns: A dictionary containing the list of messages and the timestamp of the last message
        """
        cur = self.conn.cursor()
        cur.execute("SELECT messages, profile, last_message_ts FROM conversations WHERE chat_id=?", (chat_id,))
        if row := cur.fetchone():
            messages = json.loads(row[0]) if row[0] else []
            profile = json.loads(row[1]) if row[1] else None
            last_message_ts = row[2]
            return {"messages": messages, "profile": profile, "last_message_ts": last_message_ts}

    def save_conversation(
        self, chat_id: str, messages: List[Dict[str, str]], last_message_ts: Optional[str] = None
    ) -> None:
        """Save the conversation history for a given chat_id.

        :chat_id: The unique identifier for the chat session
        :messages: A list of message dictionaries to save (each with 'role' and 'content')
        :last_message_ts: Optional timestamp of the last message (if not provided, current time will be used)
        """
        messages = messages[-self.max_entries_per_chat :]
        last_message_ts = last_message_ts or datetime.now(timezone.utc).isoformat()
        cur = self.conn.cursor()

        # Preserve existing profile
        cur.execute("SELECT profile FROM conversations WHERE chat_id=?", (chat_id,))
        row = cur.fetchone()
        profile = row[0] if row else None

        cur.execute(
            """
            INSERT INTO conversations (chat_id, messages, profile, last_message_ts)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                messages=excluded.messages,
                last_message_ts=excluded.last_message_ts
            """,
            (chat_id, json.dumps(messages), profile, last_message_ts),
        )
        self.conn.commit()

    def get_profile(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the user profile for a given chat_id.

        :chat_id: The unique identifier for the chat session
        :returns: A dictionary containing the user profile information
        """
        cur = self.conn.cursor()
        cur.execute("SELECT profile FROM conversations WHERE chat_id=?", (chat_id,))
        row = cur.fetchone()

        if row and row[0]:
            return json.loads(row[0])

    def save_profile(self, chat_id: str, profile: Dict[str, Any]) -> None:
        """Save the user profile for a given chat_id.

        :chat_id: The unique identifier for the chat session
        :profile: A dictionary containing the user profile information to save
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO conversations (chat_id, messages, profile, last_message_ts)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                profile=excluded.profile
            """,
            (chat_id, json.dumps([]), json.dumps(profile), datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

    def is_new_conversation(self, chat_id: str, threshold_minutes: int = 30) -> bool:
        """Determine if a conversation is new based on the time since the last message.

        :chat_id: The unique identifier for the chat session
        :threshold_minutes: The number of minutes to consider a conversation as "new" if no messages have been exchanged
        :returns: True if the conversation is new, False otherwise
        """
        conv = self.get_conversation(chat_id)
        if not conv or not conv["last_message_ts"]:
            return True

        last_ts = datetime.fromisoformat(conv["last_message_ts"])
        now = datetime.now(timezone.utc)
        diff = (now - last_ts).total_seconds() / 60
        return diff > threshold_minutes

import json
from pathlib import Path
from typing import Any

from jmespath import search as jsearch

from app.config import SERIALIZED_DATA_PATH
from app.utils.conversation_db import ConversationDB


class ConversationDBSerializer:
    """Utility class to serialize and deserialize the conversation database to/from JSON files."""

    def __init__(self, db: ConversationDB) -> None:
        self.db = db

    def export_all(self) -> dict[str, dict[str, Any]]:
        """Export all conversations and profiles from the database into a structured dictionary format.

        :returns: A dictionary containing all conversations and profiles, ready to be serialized to JSON.
        """

        cur = self.db.conn.cursor()
        # Export conversations
        cur.execute("SELECT chat_id, messages, profile, last_message_ts FROM conversations")
        conversations = {
            row[0]: {
                "messages": json.loads(row[1]) if row[1] else [],
                "profile": json.loads(row[2]) if row[2] else {},
                "last_message_ts": row[3],
            }
            for row in cur.fetchall()
        }

        return {"conversations": conversations}

    def export_to_file(self, path: Path = SERIALIZED_DATA_PATH) -> None:
        """Export the entire conversation database to a JSON file."""

        data = self.export_all()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def import_from_file(self, path: Path) -> None:
        """Import conversations and profiles from a JSON file into the database."""

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Import conversations
        for chat_id, conv in data.get("conversations", {}).items():
            self.db.save_conversation(chat_id, conv["messages"], conv.get("last_message_ts"))
        # Import profiles
        for chat_id, profile in jsearch("conversations.profile", data).items():
            self.db.save_profile(chat_id, profile)

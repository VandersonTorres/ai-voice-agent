import httpx
from typing import List, Dict

from app.config import OLLAMA_MODEL
from app.logging import get_logger


class OllamaClient:
    """Asynchronous client for interacting with the Ollama API"""

    def __init__(self, model: str = OLLAMA_MODEL, host: str = "http://localhost:11434") -> None:
        """Initialize the Ollama client

        :model: The name of the Ollama model to be used (e.g. llama3:8b)
        :host: The Ollama server base URL. Defaults to localhost.
        """
        self.model = model
        self.host = host
        self.logger = get_logger(self.__class__.__name__)
        self.client = httpx.AsyncClient(timeout=360)

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send a chat request to the Ollama API and return the model response

        :messages: A list of message dictionaries following the OpenAI chat format
            (each item must contain 'role' and 'content')
        :returns: The generated text response from the language model
        :raises requests.HTTPError: If the Ollama API returns an error response
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        self.logger.info(f"[LLM] Sending async request to {self.host}/api/chat")

        response = await self.client.post(
            f"{self.host}/api/chat",
            json=payload,
        )
        response.raise_for_status()

        return response.json()["message"]["content"].strip()

    async def close(self):
        await self.client.aclose()

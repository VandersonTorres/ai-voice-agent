import httpx
from typing import List, Dict

from app.config import CONVERSATIONAL_LLM
from app.logging import get_logger


class LLMClient:
    """Asynchronous client for interacting with the target LLM API"""

    def __init__(
        self, model: str = CONVERSATIONAL_LLM, host: str = "http://localhost:11434", timeout: int = 360
    ) -> None:
        """Initialize the LLM client

        :model: The name of the Model to be used (e.g. llama3:8b)
        :host: The server base URL. Defaults to localhost.
        :timeout: Time waited until break the LLM request
        """
        self.model = model
        self.host = host
        self.logger = get_logger(self.__class__.__name__)

        self.logger.info(f"Initializing LLMClient with model {self.model} at {self.host}")
        self.client = httpx.AsyncClient(timeout=timeout)

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send a chat request to the LLM API and return the model response

        :messages: A list of message dictionaries following the OpenAI chat format
            (each item must contain 'role' and 'content')
        :returns: The generated text response from the language model
        :raises requests.HTTPError: If the LLM API returns an error response
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

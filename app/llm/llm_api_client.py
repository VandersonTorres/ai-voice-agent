import httpx
from typing import List, Dict

from openai import OpenAI

from app.config import CONVERSATIONAL_LLM, IS_PRODUCTION
from app.logging import get_logger
from app.utils import run_in_thread


class LLMClient:
    """Asynchronous client for interacting with the target LLM API"""

    is_production = IS_PRODUCTION

    def __init__(self, model: str = CONVERSATIONAL_LLM, timeout: int = 30) -> None:
        """Initialize the LLM client

        :model: The name of the Model to be used (e.g. llama3:8b, gpt-4o-mini).
        :timeout: Time waited until break the LLM request
        """
        self.model = model
        self.logger = get_logger(self.__class__.__name__)

        if self.is_production:
            self.client = OpenAI(timeout=timeout)
            self.host = "openai"  # Host is not used for OpenAI client, set for logging consistency
        else:
            self.client = httpx.AsyncClient(timeout=timeout * 6)  # Longer timeout for local LLMs
            self.host = "http://localhost:11434"

        self.logger.info(f"Initialized LLMClient with model {self.model} at {self.host}")

    async def _request_dev_model(self, messages: List[Dict[str, str]]) -> str:
        """Helper method to send a request to the development LLM API and return the response content

        :raises requests.HTTPError: If the LLM API returns an error response
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        response = await self.client.post(
            f"{self.host}/api/chat",
            json=payload,
        )
        response.raise_for_status()

        return response.json()["message"]["content"].strip()

    async def _request_prod_model(self, messages: List[Dict[str, str]]) -> str:
        """
        Helper method to send a request to the production LLM API and return the response content
        """
        return await run_in_thread(self._sync_chat, messages)

    def _sync_chat(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            presence_penalty=0.6,
        )
        self.logger.info(f"[LLM] Tokens used: {response.usage.total_tokens}")
        return response.choices[0].message.content.strip()

    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send a chat request to the LLM API and return the model response

        :messages: A list of message dictionaries following the OpenAI chat format
            (each item must contain 'role' and 'content')
        :returns: The generated text response from the language model
        :raises requests.HTTPError: If the LLM API returns an error response
        """
        self.logger.info(f"[LLM] Requesting chat completion from '{self.model}'")
        if self.is_production:
            return await self._request_prod_model(messages)

        return await self._request_dev_model(messages)

    async def close(self):
        if not self.is_production:
            await self.client.aclose()

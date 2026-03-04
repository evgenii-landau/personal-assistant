from groq import AsyncGroq
from typing import List, Dict
from .base_client import BaseAIClient
import os


class GroqClient(BaseAIClient):
    """Клиент для Groq API — бесплатный, быстрый."""

    def __init__(self):
        self.client = None
        api_key = os.getenv("GROQ_API_KEY", "")
        if api_key:
            self.client = AsyncGroq(api_key=api_key)

    def is_available(self) -> bool:
        return self.client is not None

    async def chat(self, messages: List[Dict], system_prompt: str = "") -> str:
        if not self.is_available():
            raise RuntimeError("Groq API ключ не настроен")

        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)

        response = await self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=all_messages,
            max_tokens=4096,
        )
        return response.choices[0].message.content

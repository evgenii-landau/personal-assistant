import os
import anthropic
from typing import List, Dict
from .base_client import BaseAIClient

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-20241022")


class ClaudeClient(BaseAIClient):
    """Клиент для Claude API (Anthropic)."""

    def __init__(self):
        self.client = None
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key:
            self.client = anthropic.AsyncAnthropic(api_key=api_key)

    def is_available(self) -> bool:
        return self.client is not None

    async def chat(self, messages: List[Dict], system_prompt: str = "") -> str:
        if not self.is_available():
            raise RuntimeError("Claude API ключ не настроен")

        # Anthropic требует чередования user/assistant ролей
        # Убираем возможные дубли
        cleaned = []
        for msg in messages:
            if cleaned and cleaned[-1]["role"] == msg["role"]:
                cleaned[-1]["content"] += "\n" + msg["content"]
            else:
                cleaned.append(msg)

        kwargs = {
            "model": CLAUDE_MODEL,
            "max_tokens": 4096,
            "messages": cleaned,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text

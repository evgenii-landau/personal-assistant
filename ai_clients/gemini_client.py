import os
import google.generativeai as genai
from typing import List, Dict
from .base_client import BaseAIClient

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


class GeminiClient(BaseAIClient):
    """Клиент для Gemini API (Google). Бесплатный tier с большим контекстом."""

    def __init__(self):
        self.model = None
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(GEMINI_MODEL)

    def is_available(self) -> bool:
        return self.model is not None

    async def chat(self, messages: List[Dict], system_prompt: str = "") -> str:
        if not self.is_available():
            raise RuntimeError("Gemini API ключ не настроен")

        # Конвертируем формат сообщений в формат Gemini
        history = []
        for msg in messages[:-1]:  # Все кроме последнего
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        last_message = messages[-1]["content"] if messages else ""

        # Добавляем system prompt к первому сообщению если есть
        if system_prompt and history:
            history[0]["parts"][0] = f"{system_prompt}\n\n{history[0]['parts'][0]}"
        elif system_prompt and not history:
            last_message = f"{system_prompt}\n\n{last_message}"

        chat_session = self.model.start_chat(history=history)
        response = await chat_session.send_message_async(last_message)
        return response.text

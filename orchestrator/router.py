from enum import Enum
from typing import List, Dict, Tuple
from ai_clients.groq_client import GroqClient
import config


class TaskType(Enum):
    CODE = "code"
    LARGE_CONTEXT = "large_context"
    DESKTOP = "desktop"
    GENERAL = "general"


DESKTOP_KEYWORDS = [
    "заметку", "заметка", "obsidian", "файл", "папку", "создай", "открой",
    "запусти", "напоминание", "calendar", "браузер", "скачай", "найди файл",
    "рабочий стол", "терминал", "скрипт", "автоматизи"
]

CODE_KEYWORDS = [
    "код", "code", "python", "javascript", "функцию", "скрипт", "баг",
    "ошибку", "debug", "программу", "алгоритм", "class", "def ", "import",
    "github", "git", "sql", "api", "запрос", "regex"
]


class AIRouter:
    def __init__(self):
        self.groq = GroqClient()

    def classify(self, text: str, history: List[Dict]) -> TaskType:
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in DESKTOP_KEYWORDS):
            return TaskType.DESKTOP
        if any(kw in text_lower for kw in CODE_KEYWORDS):
            return TaskType.CODE
        if len(text) > 2000 or len(history) > 10:
            return TaskType.LARGE_CONTEXT
        
        return TaskType.GENERAL

    def select_ai(self, task_type: TaskType) -> Tuple:
        # Всегда используем Groq
        return self.groq, "Groq"

    async def process(self, text: str, history: List[Dict], system_prompt: str = "") -> dict:
        task_type = self.classify(text, history)
        ai_client, ai_name = self.select_ai(task_type)
        
        messages = history + [{"role": "user", "content": text}]
        response = await ai_client.chat(messages, system_prompt)
        
        return {
            "response": response,
            "ai_used": ai_name,
            "task_type": task_type.value
        }

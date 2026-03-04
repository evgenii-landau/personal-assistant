from abc import ABC, abstractmethod
from typing import List, Dict


class BaseAIClient(ABC):
    """Базовый класс для всех AI клиентов."""

    @abstractmethod
    async def chat(self, messages: List[Dict], system_prompt: str = "") -> str:
        """
        Отправить сообщения и получить ответ.
        
        messages: [{"role": "user"/"assistant", "content": "..."}]
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Проверить, настроен ли клиент (есть ли API ключ)."""
        pass

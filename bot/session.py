from typing import List, Dict
from collections import defaultdict

# Максимум сообщений в истории на пользователя
MAX_HISTORY_LENGTH = 20


class SessionManager:
    """Хранит историю диалога для каждого пользователя в памяти."""

    def __init__(self):
        # user_id → список сообщений
        self._sessions: Dict[int, List[Dict]] = defaultdict(list)

    def get_history(self, user_id: int) -> List[Dict]:
        return list(self._sessions[user_id])

    def add_message(self, user_id: int, role: str, content: str):
        """Добавить сообщение в историю. role: 'user' или 'assistant'."""
        self._sessions[user_id].append({"role": role, "content": content})

        # Обрезаем историю если слишком длинная
        if len(self._sessions[user_id]) > MAX_HISTORY_LENGTH:
            # Оставляем последние MAX_HISTORY_LENGTH сообщений
            self._sessions[user_id] = self._sessions[user_id][-MAX_HISTORY_LENGTH:]

    def clear(self, user_id: int):
        """Очистить историю диалога."""
        self._sessions[user_id] = []

    def summary(self, user_id: int) -> str:
        count = len(self._sessions[user_id])
        return f"{count} сообщений в истории"


# Глобальный экземпляр
session_manager = SessionManager()

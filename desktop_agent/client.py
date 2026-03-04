"""
Клиент для Desktop Agent — вызывается из оркестратора
когда нужно выполнить действие на Mac.
"""

import httpx
import logging
from typing import Optional
import config

logger = logging.getLogger(__name__)


class DesktopAgentClient:

    def __init__(self):
        self.base_url = config.DESKTOP_AGENT_URL
        self.headers = {"x-secret": config.DESKTOP_AGENT_SECRET}

    async def _post(self, endpoint: str, data: dict) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=self.headers
            )
            resp.raise_for_status()
            return resp.json()

    async def is_running(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    f"{self.base_url}/health",
                    headers=self.headers
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def create_note(self, title: str, content: str, folder: Optional[str] = None) -> dict:
        return await self._post("/obsidian/note", {
            "title": title,
            "content": content,
            "folder": folder
        })

    async def open_url(self, url: str) -> dict:
        return await self._post("/open/url", {"command": url})

    async def write_file(self, path: str, content: str) -> dict:
        return await self._post("/file/write", {"path": path, "content": content})

    async def run_applescript(self, script: str) -> dict:
        return await self._post("/applescript", {"command": script})

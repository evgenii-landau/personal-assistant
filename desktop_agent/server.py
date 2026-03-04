"""
Desktop Agent — локальный FastAPI сервер.
Запускается отдельно от бота, принимает команды и выполняет их на Mac.

Запуск: python desktop_agent/server.py
"""

import subprocess
import os
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import uvicorn

import sys
sys.path.append(str(Path(__file__).parent.parent))
import config

logger = logging.getLogger(__name__)
app = FastAPI(title="Personal Assistant — Desktop Agent")


# ── Auth ──────────────────────────────────────────────────
def verify_secret(x_secret: str = Header(...)):
    if x_secret != config.DESKTOP_AGENT_SECRET:
        raise HTTPException(status_code=403, detail="Неверный секретный ключ")


# ── Schemas ───────────────────────────────────────────────
class NoteRequest(BaseModel):
    title: str
    content: str
    folder: Optional[str] = None  # Относительный путь внутри Vault


class FileRequest(BaseModel):
    path: str
    content: Optional[str] = None


class CommandRequest(BaseModel):
    command: str  # Shell команда (осторожно!)


# ── Endpoints ─────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "vault": config.OBSIDIAN_VAULT_PATH}


@app.post("/obsidian/note")
async def create_obsidian_note(req: NoteRequest, x_secret: str = Header(...)):
    verify_secret(x_secret)

    vault = Path(config.OBSIDIAN_VAULT_PATH)
    if not vault.exists():
        raise HTTPException(400, f"Vault не найден: {vault}")

    # Определяем папку
    if req.folder:
        note_dir = vault / req.folder
    else:
        note_dir = vault

    note_dir.mkdir(parents=True, exist_ok=True)

    # Создаём файл заметки
    safe_title = req.title.replace("/", "-").replace("\\", "-")
    note_path = note_dir / f"{safe_title}.md"

    note_path.write_text(req.content, encoding="utf-8")
    logger.info(f"Создана заметка: {note_path}")

    return {"status": "created", "path": str(note_path)}


@app.get("/obsidian/list")
async def list_obsidian_notes(folder: str = "", x_secret: str = Header(...)):
    verify_secret(x_secret)

    vault = Path(config.OBSIDIAN_VAULT_PATH)
    search_dir = vault / folder if folder else vault

    if not search_dir.exists():
        raise HTTPException(400, f"Папка не найдена: {search_dir}")

    notes = [
        str(p.relative_to(vault))
        for p in search_dir.rglob("*.md")
    ]
    return {"notes": notes, "count": len(notes)}


@app.post("/file/write")
async def write_file(req: FileRequest, x_secret: str = Header(...)):
    verify_secret(x_secret)

    path = Path(req.path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(req.content or "", encoding="utf-8")

    return {"status": "written", "path": str(path)}


@app.get("/file/read")
async def read_file(path: str, x_secret: str = Header(...)):
    verify_secret(x_secret)

    file_path = Path(path).expanduser()
    if not file_path.exists():
        raise HTTPException(404, "Файл не найден")

    content = file_path.read_text(encoding="utf-8")
    return {"content": content, "path": str(file_path)}


@app.post("/applescript")
async def run_applescript(req: CommandRequest, x_secret: str = Header(...)):
    """Выполнить AppleScript команду (открыть приложение, управлять системой)."""
    verify_secret(x_secret)

    result = subprocess.run(
        ["osascript", "-e", req.command],
        capture_output=True, text=True, timeout=30
    )

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }


@app.post("/open/url")
async def open_url(req: CommandRequest, x_secret: str = Header(...)):
    """Открыть URL в браузере по умолчанию."""
    verify_secret(x_secret)
    subprocess.run(["open", req.command])
    return {"status": "opened", "url": req.command}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("🖥️  Desktop Agent запущен на http://localhost:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")

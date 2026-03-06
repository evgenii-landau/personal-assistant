"""
telegram_bot/main.py
────────────────────
Aiogram-based Telegram bot skeleton.

This bot communicates exclusively with the FastAPI backend.
It never accesses the database directly.

Run: python -m telegram_bot.main
"""
import asyncio
import logging
import os

import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ── Helpers ───────────────────────────────────────────────────────────────────

async def backend_get(path: str, token: str) -> dict | None:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BACKEND_URL}{path}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error(f"Backend GET {path} failed: {e}")
        return None


async def backend_post(path: str, payload: dict, token: str | None = None) -> dict | None:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BACKEND_URL}{path}",
                json=payload,
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error(f"Backend POST {path} failed: {e}")
        return None


# ── Handlers ──────────────────────────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Finance bot is running.\n\n"
        "Commands:\n"
        "/start — welcome\n"
        "/help  — help\n"
        "/status — backend status"
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Available commands:\n"
        "/start  — welcome message\n"
        "/help   — this help\n"
        "/status — check backend status"
    )


@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BACKEND_URL}/health", timeout=5)
            data = resp.json()
            await message.answer(f"Backend: {data.get('status', 'unknown')}")
    except Exception:
        await message.answer("Backend is unreachable.")


@dp.message()
async def handle_text(message: types.Message):
    # Placeholder: forward to backend or process locally
    await message.answer(f"Received: {message.text}")


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    logger.info("Starting aiogram bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

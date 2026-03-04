import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ALLOWED_USER_ID = int(os.getenv("TELEGRAM_ALLOWED_USER_ID", "0"))

# ── AI APIs ───────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Desktop Agent ─────────────────────────────────────────
DESKTOP_AGENT_URL = os.getenv("DESKTOP_AGENT_URL", "http://localhost:8001")
DESKTOP_AGENT_SECRET = os.getenv("DESKTOP_AGENT_SECRET", "")

# ── Obsidian ──────────────────────────────────────────────
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "")

# ── Google Sheets ─────────────────────────────────────────
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "credentials.json")
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")

# ── AI Router settings ────────────────────────────────────
# Пороговое значение токенов — если больше, используем Gemini
LARGE_CONTEXT_THRESHOLD = 10_000

# Модели
CLAUDE_MODEL = "claude-3-5-haiku-20241022"   # Быстрый и дешёвый для большинства задач
GEMINI_MODEL = "gemini-2.0-flash"             # Бесплатный, большой контекст

# ── Validation ────────────────────────────────────────────
def validate_config():
    errors = []
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN не задан")
    if not TELEGRAM_ALLOWED_USER_ID:
        errors.append("TELEGRAM_ALLOWED_USER_ID не задан")
    if not ANTHROPIC_API_KEY and not GEMINI_API_KEY:
        errors.append("Нужен хотя бы один AI API ключ (ANTHROPIC или GEMINI)")
    return errors

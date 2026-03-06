# Running the Project

## Setup (first time)

```bash
cp .env.example .env       # fill in all required values
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Place your Google service account JSON at the path set in `GOOGLE_SHEETS_CREDENTIALS` (default: `google_credentials.json` in the project root).

## Required env vars

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `TELEGRAM_ALLOWED_USER_ID` | Your Telegram numeric user ID |
| `GROQ_API_KEY` | Primary AI + voice transcription |
| `GOOGLE_SHEETS_CREDENTIALS` | Path to service account JSON (default: `google_credentials.json`) |
| `GOOGLE_SHEETS_ID` | Spreadsheet ID from the URL |
| `DESKTOP_AGENT_SECRET` | Any random string — shared between bot and desktop agent |
| `OBSIDIAN_VAULT_PATH` | Absolute path to Obsidian vault folder |

Optional (unused by default, kept for future multi-model routing):
`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `TAVILY_API_KEY`, `EXCHANGERATE_API_KEY`

## Running

```bash
# Both services together
./start.sh

# Or separately (two terminals)
source venv/bin/activate
PYTHONPATH=. python desktop_agent/server.py   # Terminal 1
PYTHONPATH=. python bot/main.py               # Terminal 2
```

`PYTHONPATH=.` is required so that `import config` resolves from the project root.

## Logs

Written to both stdout and `assistant.log` in the project root.

## Startup validation

`bot/main.py` calls `config.validate_config()` on startup. It checks:
- `TELEGRAM_BOT_TOKEN` is set
- `TELEGRAM_ALLOWED_USER_ID` is set
- `GROQ_API_KEY` is set

Missing values will print errors and exit before connecting to Telegram.

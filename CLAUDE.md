# Personal Finance AI Assistant

## Project Purpose

A personal finance assistant delivered via Telegram. The user logs income and expenses in natural language, tracks budgets, and views analytics. The system is single-user and self-hosted.

---

## Architecture

```
Telegram user
     │
     ▼
telegram_bot/          ← aiogram bot, HTTP-only, no DB access
     │  httpx
     ▼
backend/               ← FastAPI + PostgreSQL (the source of truth)
     │
     ▼
PostgreSQL             ← transactions, users (via Docker)
```

AI clients (`ai_clients/`) are available for use in the bot or backend.
The backend never calls AI directly — AI logic belongs in the bot or a dedicated service.

---

## Folder Structure

```
backend/
├── main.py                    FastAPI app entry point, router registration
├── core/
│   ├── deps.py                JWT dependency: get_current_user
│   └── security.py            bcrypt hashing, JWT create/decode (7-day tokens)
├── db/
│   └── database.py            SQLAlchemy engine, SessionLocal, Base, get_db()
├── models/
│   ├── user.py                User(id, email, hashed_password, telegram_id)
│   └── transaction.py         Transaction(id, user_id, amount, currency, amount_rub,
│                                          category, description, type, account)
├── routers/
│   ├── auth.py                POST /auth/register, POST /auth/login,
│   │                          POST /auth/link-telegram
│   ├── transactions.py        CRUD /transactions/
│   └── analytics.py           GET /analytics/dashboard
├── schemas/
│   ├── user.py                UserCreate, UserOut, Token, LinkTelegramRequest
│   └── transaction.py         TransactionCreate, TransactionUpdate, TransactionOut
└── services/
    ├── auth_service.py        register_user, authenticate_user, link_telegram
    └── transaction_service.py create/list/get/update/delete_transaction, get_dashboard

telegram_bot/
└── main.py                    aiogram Dispatcher, /start /help /status handlers,
                               backend_get() / backend_post() helpers

ai_clients/
├── base_client.py             BaseAIClient ABC: is_available(), chat()
├── claude_client.py           Anthropic — claude-3-5-haiku (env: CLAUDE_MODEL)
├── gemini_client.py           Google Gemini — gemini-2.0-flash (env: GEMINI_MODEL)
└── groq_client.py             Groq — llama-3.3-70b-versatile

agent_docs/                    Architecture and planning docs
docker-compose.yml             Services: db (postgres:15), backend (port 8000)
Dockerfile.backend             python:3.11-slim, installs requirements, runs uvicorn
requirements.txt               All Python dependencies
.env.example                   Environment variable template
```

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Create account (email + password) |
| POST | `/auth/login` | — | Returns Bearer JWT |
| POST | `/auth/link-telegram` | JWT | Link Telegram user ID to account |
| GET | `/transactions/` | JWT | List all transactions for user |
| POST | `/transactions/` | JWT | Create transaction |
| GET | `/transactions/{id}` | JWT | Get single transaction |
| PUT | `/transactions/{id}` | JWT | Update transaction |
| DELETE | `/transactions/{id}` | JWT | Delete transaction |
| GET | `/analytics/dashboard` | JWT | Spending summary |
| GET | `/health` | — | Backend liveness check |

---

## Environment Variables

```env
# Telegram
TELEGRAM_BOT_TOKEN=

# AI APIs
GROQ_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=

# Backend
DATABASE_URL=postgresql://finance_user:finance_pass@localhost:5432/finance_db
SECRET_KEY=                    # long random string
BACKEND_URL=http://localhost:8000

# Optional — override default model names
CLAUDE_MODEL=claude-3-5-haiku-20241022
GEMINI_MODEL=gemini-2.0-flash
```

---

## Running Locally

**Prerequisites:** Python 3.11+, PostgreSQL running locally or via Docker.

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in values

# Start backend
uvicorn backend.main:app --reload --port 8000

# Start bot (separate terminal)
python -m telegram_bot.main
```

Tables are created automatically at startup via `Base.metadata.create_all()`.

---

## Running with Docker

```bash
cp .env.example .env   # fill in SECRET_KEY at minimum

docker compose up --build
```

This starts:
- `db` — PostgreSQL 15 on port 5432
- `backend` — FastAPI on port 8000

The bot runs outside Docker (it needs a valid `TELEGRAM_BOT_TOKEN`):

```bash
source venv/bin/activate
BACKEND_URL=http://localhost:8000 python -m telegram_bot.main
```

---

## Data Model Notes

- `Transaction.type` is `"income"` or `"expense"` (string, not enum)
- `Transaction.amount` stores the original amount; `amount_rub` stores the RUB-converted amount
- `Transaction.currency` is a 3-letter ISO code (e.g. `"RUB"`, `"USD"`)
- `User.telegram_id` is nullable — linked after registration via `/auth/link-telegram`

---

## Coding Conventions

- All business logic lives in `backend/services/`, not in routers
- Routers only validate input, call a service, and return the result
- Use `Depends(get_current_user)` for all authenticated endpoints
- Use `Depends(get_db)` for all database access — never create a session manually
- AI clients read API keys from `os.getenv()` directly — no central config module
- Keep changes small and targeted; do not refactor working code unless asked
- Do not add comments unless the logic is non-obvious

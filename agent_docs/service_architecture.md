# Service Architecture

## Two processes

The system runs as two separate processes. Start both with `./start.sh`.

| Process | Entry point | Port |
|---|---|---|
| Telegram Bot | `bot/main.py` | — |
| Desktop Agent | `desktop_agent/server.py` | 8001 |

## Dependency graph

```
config.py                   ← single source of truth for all env vars
    │
    ├── ai_clients/         ← BaseAIClient + Groq (active), Claude, Gemini
    │     └── groq_client   ← always used by router
    │
    ├── orchestrator/router.py   ← wraps AI client, classifies task type
    │
    ├── desktop_agent/
    │     ├── server.py     ← standalone FastAPI process on :8001
    │     └── client.py     ← HTTP client called from handlers
    │
    ├── tools/finance/      ← Google Sheets backed finance system
    │     ├── client.py     ← singleton gspread connection
    │     ├── constants.py  ← categories, column indexes, timezone
    │     ├── transactions.py
    │     ├── accounts.py   ← balances + piggy bank (computed from transactions)
    │     ├── budgets.py
    │     ├── reports.py
    │     ├── sheets_sync.py← full_sync() called after every mutation
    │     └── __init__.py   ← public API (only this is imported externally)
    │
    ├── tools/              ← stateless integrations
    │     ├── search.py     ← Tavily (lazy client init)
    │     ├── currency.py   ← ExchangeRate.host + NBG
    │     └── voice.py      ← Groq Whisper
    │
    └── bot/
          ├── session.py    ← in-memory history per user (20 msg cap)
          ├── handlers.py   ← central dispatcher (all routing logic lives here)
          └── main.py       ← registers handlers, starts polling
```

No circular dependencies. `config.py` has no project imports. `tools/` have no project imports (they read env vars directly via `os.getenv` — safe because `config.py` calls `load_dotenv()` before any tool is imported).

## Request flow

```
Telegram message
    └─ bot/handlers.py :: process_text()
          │
          ├─ analyze_message(text, ai_client)
          │     └─ Groq classifies intent:
          │           add_transaction / get_report / set_budget / other / ...
          │
          ├─ Finance intent  → tools/finance/  (Google Sheets)
          ├─ Currency query  → tools/currency.py  (then injected into AI prompt)
          ├─ Search needed   → tools/search.py    (then injected into AI prompt)
          │
          └─ General / "other"
                └─ orchestrator/router.py :: process()
                      └─ ai_clients/groq_client.py
                            │
                            └─ Response contains OBSIDIAN_NOTE block?
                                  └─ desktop_agent/client.py ──HTTP──► :8001
```

Voice messages follow the same path — `handle_voice()` transcribes with Groq Whisper, then calls `process_text()` with the resulting text.

## Key design rules

- **`bot/handlers.py` is the only dispatcher.** All routing logic lives there. Tools and AI clients do not call each other.
- **`tools/finance/__init__.py` is the only public API** for the finance module. External code imports from there, never from submodules directly.
- **Google Sheets is the only persistent store.** Session history is in-memory and resets on restart.
- **Python writes only raw values to Sheets.** Formatting, colors, and charts are handled by Google Apps Script on the spreadsheet side.
- **Desktop agent is stateless.** It validates the secret header and executes; it has no knowledge of the bot's state.

## Known limitations / future work

- `AIRouter.classify()` computes a task type (CODE, DESKTOP, LARGE_CONTEXT, GENERAL) but `select_ai()` currently always returns Groq regardless. The classification is preserved for when multi-model routing is restored.
- `tools/` integrations (search, currency, voice) bypass `config.py` and read env vars directly. This works because `load_dotenv()` runs at `config.py` import time. A future cleanup could add these keys to `config.py` for uniformity.
- `FINANCE_CATEGORIES` in `bot/handlers.py` duplicates `CATEGORIES` in `tools/finance/constants.py`. These must be kept in sync manually.

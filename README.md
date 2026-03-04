# 🤖 Personal AI Assistant

Персональный AI-ассистент в Telegram с маршрутизацией между моделями и управлением Mac.

---

## 📋 Структура проекта

```
personal-assistant/
├── bot/
│   ├── main.py          # Точка входа Telegram бота
│   ├── handlers.py      # Обработчики сообщений и команд
│   └── session.py       # История диалога в памяти
├── orchestrator/
│   └── router.py        # Маршрутизатор — выбирает нужный AI
├── ai_clients/
│   ├── base_client.py   # Базовый класс
│   ├── claude_client.py # Клиент Claude (Anthropic)
│   └── gemini_client.py # Клиент Gemini (Google)
├── desktop_agent/
│   ├── server.py        # Локальный FastAPI сервер
│   └── client.py        # Клиент для вызова агента
├── config.py            # Конфигурация
├── requirements.txt
├── .env.example         # Шаблон переменных окружения
└── start.sh             # Скрипт запуска всего
```

---

## 🚀 Установка и запуск

### Шаг 1 — Получи Telegram Bot Token

1. Открой Telegram, найди **@BotFather**
2. Напиши `/newbot`
3. Придумай имя и username для бота
4. Скопируй токен — он выглядит так: `7123456789:AAFxxxxxx`

### Шаг 2 — Узнай свой Telegram User ID

1. Напиши боту **@userinfobot** в Telegram
2. Он пришлёт твой ID (число вроде `123456789`)

### Шаг 3 — Получи API ключи

**Claude (Anthropic):**
- Зайди на https://console.anthropic.com
- Зарегистрируйся → API Keys → Create Key
- При регистрации дают $5 кредитов

**Gemini (Google) — бесплатно:**
- Зайди на https://aistudio.google.com
- Нажми "Get API Key" → Create API key
- Полностью бесплатно (1500 запросов/день)

### Шаг 4 — Настрой окружение

```bash
# Клонируй или скопируй папку проекта
cd personal-assistant

# Скопируй шаблон конфига
cp .env.example .env

# Открой .env в любом редакторе и заполни все поля
nano .env
# или
open -a TextEdit .env
```

Заполни в `.env`:
```
TELEGRAM_BOT_TOKEN=твой_токен_от_BotFather
TELEGRAM_ALLOWED_USER_ID=твой_user_id
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
DESKTOP_AGENT_SECRET=придумай_любую_строку_например_mySecret123
OBSIDIAN_VAULT_PATH=/Users/твоё_имя/Documents/MyVault
```

### Шаг 5 — Запуск

```bash
chmod +x start.sh
./start.sh
```

Или вручную (в двух терминалах):
```bash
# Терминал 1 — Desktop Agent
source venv/bin/activate
python desktop_agent/server.py

# Терминал 2 — Telegram Bot
source venv/bin/activate
python bot/main.py
```

---

## 💬 Как пользоваться

Просто пиши боту в Telegram:

| Что написать | Что произойдёт |
|---|---|
| `Объясни как работает async/await` | Claude ответит на вопрос |
| `Напиши функцию сортировки на Python` | Claude напишет код |
| `Создай заметку "Идеи проекта" с текстом...` | Создаст .md файл в Obsidian |
| `Создай заметку в папке Work/Meetings с названием...` | Создаст в нужной папке |
| `Проанализируй этот большой текст: [текст]` | Gemini обработает большой контекст |

**Команды:**
- `/start` — приветствие и список возможностей
- `/reset` — очистить историю диалога
- `/status` — статус подключённых AI

---

## 🔧 Логика маршрутизации AI

```
Запрос пользователя
       ↓
Есть слова: заметку/файл/obsidian/открой?
       ↓ Да → Desktop Agent + Claude для ответа
       ↓ Нет
Есть слова: код/python/функцию/баг?
       ↓ Да → Claude
       ↓ Нет
Контекст > 10,000 символов?
       ↓ Да → Gemini (большой контекст)
       ↓ Нет → Claude (общие задачи)
```

---

## 📈 Этапы разработки

- [x] **Этап 1** — Архитектура и скелет проекта
- [x] **Этап 2** — Claude + Gemini клиенты и маршрутизатор
- [x] **Этап 3** — Desktop Agent (Obsidian, файлы, AppleScript)
- [ ] **Этап 4** — Голосовые сообщения
- [ ] **Этап 5** — Работа с изображениями
- [ ] **Этап 6** — Долгосрочная память (ChromaDB)
- [ ] **Этап 7** — Напоминания и календарь

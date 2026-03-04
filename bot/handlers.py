import os
import json
import logging
import re
from telegram.constants import ChatAction

from bot.session import session_manager
from orchestrator.router import AIRouter
from desktop_agent.client import DesktopAgentClient
from tools.search import web_search, should_search
from tools.currency import format_currency_info, is_currency_query
from tools.voice import transcribe
from tools.spotify import handle_spotify_command
from tools.finance import (
    add_transaction, get_monthly_report, get_budget_status,
    set_budget, get_balance, undo_last_transaction, remove_budget,
    compare_with_previous_month
)
import config

logger = logging.getLogger(__name__)
router = AIRouter()
desktop = DesktopAgentClient()

SYSTEM_PROMPT = """Ты — персональный AI-ассистент. Отвечай на языке пользователя.
Будь лаконичен. Не используй вступления типа "Конечно!" или "Отличный вопрос!".

ВАЖНО — когда тебе предоставлены результаты поиска или курсы валют:
1. Сравни данные между источниками
2. Если данные совпадают — дай уверенный ответ с цифрами
3. Если данные расходятся — покажи разброс
4. Всегда указывай источник и дату данных
5. Никогда не выдумывай цифры

Если пользователь просит создать заметку в Obsidian — отвечай СТРОГО в таком формате:
OBSIDIAN_NOTE
title:Название заметки
folder:
content:Текст заметки здесь
END_NOTE"""

FINANCE_CATEGORIES = [
    # Ежедневные
    "🛒 Еда и продукты",
    "🍽️ Кафе и рестораны",
    "🚕 Транспорт",
    # Регулярные
    "🏠 Жильё и коммуналки",
    "📱 Подписки",
    "💊 Здоровье",
    "💇 Красота и уход",
    # Периодические
    "🎉 Развлечения",
    "👕 Одежда",
    "📚 Образование",
    "🎁 Подарки",
    # Редкие
    "💻 Техника и гаджеты",
    "✈️ Путешествия",
    "💼 Работа и бизнес",
    "🔧 Ремонт и обслуживание",
    "💰 Инвестиции и сбережения",
    # Специальные
    "💸 Переводы",
    "💵 Доход",
    "❓ Разное"
]


def is_allowed(user_id):
    if config.TELEGRAM_ALLOWED_USER_ID == 0:
        return True
    return user_id == config.TELEGRAM_ALLOWED_USER_ID


def parse_obsidian_command(text):
    if "OBSIDIAN_NOTE" not in text:
        return None
    title_match = re.search(r"title:(.+)", text)
    folder_match = re.search(r"folder:(.*)", text)
    content_match = re.search(r"content:([\s\S]+?)END_NOTE", text)
    title = title_match.group(1).strip() if title_match else "Заметка"
    folder = folder_match.group(1).strip() if folder_match else ""
    content = content_match.group(1).strip() if content_match else ""
    return {"title": title, "folder": folder if folder else None, "content": content}


async def analyze_message(text: str, ai_client) -> dict:
    """Определяем intent + категорию одновременно"""
    categories_str = "\n".join(FINANCE_CATEGORIES)

    prompt = f"""Проанализируй сообщение пользователя. Ответь ТОЛЬКО валидным JSON без markdown и пояснений.

Сообщение: "{text}"

Определи:
1. intent — намерение пользователя:
   - "add_transaction" — добавить трату/доход (потратил, купил, заплатил, получил, заработал)
   - "get_report" — отчёт за месяц (отчёт, статистика, сколько потратил)
   - "compare_months" — сравнить с прошлым месяцем (сравни с прошлым месяцем, динамика, как изменились траты)
   - "set_budget" — установить бюджет (установи, поставь, задай бюджет)
   - "remove_budget" — удалить бюджет одной категории (удали бюджет на еду, сбрось лимит на транспорт)
   - "clear_all_budgets" — обнулить ВСЕ бюджеты (убери все бюджеты, сбрось все лимиты, обнули все бюджеты)
   - "get_budget" — посмотреть бюджеты (покажи бюджет, статус бюджета)
   - "get_balance" — узнать баланс (баланс, сколько денег, остаток)
   - "undo" — отменить последнюю транзакцию (отмени последнюю, ошибся, удали последнюю запись)
   - "get_piggy_bank" — посмотреть копилку (копилка, сколько в копилке, баланс копилки)
   - "add_to_piggy" — положить в копилку (положи в копилку, добавь в копилку)
   - "withdraw_piggy" — снять из копилки (сними из копилки, возьми из копилки)
   - "spotify" — управление музыкой
   - "other" — всё остальное

2. category — категория или список категорий из списка (только для финансовых операций):
{categories_str}

Формат ответа:
{{"intent": "set_budget", "category": "🚕 Транспорт", "confidence": 0.97}}
или для нескольких категорий:
{{"intent": "set_budget", "categories": ["🛒 Еда и продукты", "🚕 Транспорт", "🏠 Жильё и коммуналки"], "confidence": 0.95}}

Если категория не нужна (intent = other/spotify/get_report/compare_months/get_balance/undo) — верни category: null"""

    try:
        messages = [{"role": "user", "content": prompt}]
        response = await ai_client.chat(messages, "")
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        logger.error(f"Ошибка analyze_message: {e}")
        return {"intent": "other", "category": None, "confidence": 0.0}


async def parse_transaction_with_ai(text: str, ai_client) -> dict:
    """Парсит транзакцию через AI"""
    categories_str = "\n".join(FINANCE_CATEGORIES)

    prompt = f"""Извлеки данные о финансовой транзакции. Ответь ТОЛЬКО валидным JSON без markdown.

Сообщение: "{text}"

Определи:
1. amount — сумма (число, без валюты). Распознавай сленг: "полтинник"=50, "сотка"=100, "косарь"=1000, "штука"=1000
2. category — категория из списка:
{categories_str}
3. description — краткое описание (1-3 слова, что купил/оплатил)
4. type — тип операции:
   - "expense" если трата (потратил, купил, заплатил, оплатил)
   - "income" если доход (получил, заработал, зарплата, перевели)

Примеры:
"потратил полтинник на такси" → {{"amount": 50, "category": "🚕 Транспорт", "description": "такси", "type": "expense"}}
"купил продукты за 2500" → {{"amount": 2500, "category": "🛒 Еда и продукты", "description": "продукты", "type": "expense"}}
"получил зарплату 80000" → {{"amount": 80000, "category": "💵 Доход", "description": "зарплата", "type": "income"}}

Формат ответа:
{{"amount": 500, "category": "🚕 Транспорт", "description": "такси", "type": "expense"}}"""

    try:
        messages = [{"role": "user", "content": prompt}]
        response = await ai_client.chat(messages, "")
        clean = response.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        logger.error(f"Ошибка parse_transaction_with_ai: {e}")
        return None


async def process_text(update, context, text, prefix=""):
    user_id = update.effective_user.id
    history = session_manager.get_history(user_id)

    ai_client, _ = router.select_ai(router.classify(text, history))
    analysis = await analyze_message(text, ai_client)

    intent = analysis.get("intent", "other")
    category = analysis.get("category")
    confidence = analysis.get("confidence", 0.0)

    logger.info(f"Intent: {intent} | Category: {category} | Confidence: {confidence} | Text: {text}")

    response = None

    if intent == "get_balance":
        response = await get_balance()

    elif intent == "undo":
        response = await undo_last_transaction()

    elif intent == "clear_all_budgets":
        from tools.finance import clear_all_budgets
        response = await clear_all_budgets(text)

    elif intent == "remove_budget":
        if not category or category == "❓ Разное":
            cats = "\n".join([f"• {c}" for c in FINANCE_CATEGORIES
                              if c not in ["💵 Доход", "💸 Переводы", "❓ Разное"]])
            response = f"❌ Не понял категорию. Уточни, например:\n{cats}"
        else:
            response = await remove_budget(text, category=category)

    elif intent == "set_budget":
        # Проверяем, есть ли список категорий
        categories = analysis.get("categories", [])
        if categories:
            # Устанавливаем бюджет для нескольких категорий
            results = []
            for cat in categories:
                result = await set_budget(text, category=cat)
                results.append(result)
            response = "\n\n".join(results)
        elif not category or category == "❓ Разное":
            cats = "\n".join([f"• {c}" for c in FINANCE_CATEGORIES
                              if c not in ["💵 Доход", "💸 Переводы", "❓ Разное"]])
            response = f"❌ Не понял категорию. Уточни, например:\n{cats}"
        else:
            response = await set_budget(text, category=category)

    elif intent == "get_budget":
        response = await get_budget_status()

    elif intent == "get_report":
        response = await get_monthly_report()

    elif intent == "compare_months":
        response = await compare_with_previous_month()

    elif intent == "add_transaction":
        from tools.currency import get_rates
        rates = await get_rates("RUB", ["GEL", "USD", "EUR"])
        rate_map = {
            "RUB": 1.0,
            "GEL": 1.0 / rates.get("RUBGEL", 0.037) if rates.get("RUBGEL") else 27.0,
            "USD": 1.0 / rates.get("RUBUSD", 0.011) if rates.get("RUBUSD") else 90.0,
            "EUR": 1.0 / rates.get("RUBEUR", 0.010) if rates.get("RUBEUR") else 98.0,
        }
        
        parsed_data = await parse_transaction_with_ai(text, ai_client)
        
        if not parsed_data:
            response = "❌ Не удалось распознать транзакцию. Попробуй: 'потратил 500 руб на еду'"
        else:
            currency = "RUB"
            if "gel" in text.lower() or "лари" in text.lower():
                currency = "GEL"
            elif "usd" in text.lower() or "долл" in text.lower():
                currency = "USD"
            elif "eur" in text.lower() or "евро" in text.lower():
                currency = "EUR"
            
            rate = rate_map.get(currency, 1.0)
            response = await add_transaction(text, rate, parsed_data=parsed_data)

    elif intent == "get_piggy_bank":
        from tools.finance import get_piggy_bank_balance
        response = await get_piggy_bank_balance()

    elif intent == "add_to_piggy":
        from tools.finance import add_to_piggy_bank
        import re
        match = re.search(r"(\d[\d\s]*(?:[.,]\d+)?)", text)
        if match:
            amount = float(match.group(1).replace(',', '.').replace(' ', ''))
            response = await add_to_piggy_bank(amount)
        else:
            response = "❌ Укажи сумму. Пример: положи в копилку 5000"

    elif intent == "withdraw_piggy":
        from tools.finance import withdraw_from_piggy_bank
        import re
        match = re.search(r"(\d[\d\s]*(?:[.,]\d+)?)", text)
        if match:
            amount = float(match.group(1).replace(',', '.').replace(' ', ''))
            response = await withdraw_from_piggy_bank(amount)
        else:
            response = "❌ Укажи сумму. Пример: сними из копилки 3000"

    elif intent == "spotify":
        response = await handle_spotify_command(text)

    else:
        enriched_text = text
        search_was_done = False

        if is_currency_query(text):
            await update.message.reply_text("💱 Получаю актуальные курсы...")
            currency_info = await format_currency_info(text)
            enriched_text = f"{text}\n\n[Актуальные курсы валют:\n{currency_info}]"
            search_was_done = True
        elif should_search(text):
            await update.message.reply_text("🔍 Ищу актуальную информацию...")
            search_results = await web_search(text)
            enriched_text = f"{text}\n\n[Результаты поиска:\n{search_results}]"
            search_was_done = True

        result = await router.process(enriched_text, history, SYSTEM_PROMPT)
        response = result["response"]

        obsidian_cmd = parse_obsidian_command(response)
        if obsidian_cmd:
            if not await desktop.is_running():
                await update.message.reply_text("❌ Desktop Agent не запущен.")
                return
            await desktop.create_note(
                title=obsidian_cmd["title"],
                content=obsidian_cmd["content"],
                folder=obsidian_cmd["folder"]
            )
            folder_info = f" в папке `{obsidian_cmd['folder']}`" if obsidian_cmd["folder"] else ""
            response = f"✅ Заметка **{obsidian_cmd['title']}**{folder_info} создана в Obsidian!"

        session_manager.add_message(user_id, "user", text)
        session_manager.add_message(user_id, "assistant", response)
        ai_label = f"\n\n_via {result['ai_used']}_"
        await update.message.reply_text(prefix + response + ai_label, parse_mode="Markdown")
        return

    if response:
        session_manager.add_message(user_id, "user", text)
        session_manager.add_message(user_id, "assistant", response)
        await update.message.reply_text(prefix + response, parse_mode="Markdown")


async def handle_message(update, context):
    user_id = update.effective_user.id
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if not is_allowed(user_id):
        await update.message.reply_text("⛔ Доступ запрещён.")
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    try:
        await process_text(update, context, text)
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def handle_voice(update, context):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    await update.message.reply_text("🎙️ Транскрибирую...")
    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        file_path = f"/tmp/voice_{user_id}_{voice.file_id}.ogg"
        await file.download_to_drive(file_path)
        text = await transcribe(file_path)
        os.remove(file_path)
        if not text:
            await update.message.reply_text("❌ Не удалось распознать речь.")
            return
        prefix = f"🎙️ *Распознано:* _{text}_\n\n"
        await process_text(update, context, text, prefix=prefix)
    except Exception as e:
        logger.error(f"Ошибка голосового: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def handle_start(update, context):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        return
    name = update.effective_user.first_name or "друг"
    await update.message.reply_text(
        f"👋 Привет, {name}!\n\n"
        f"Я твой персональный AI-ассистент:\n"
        f"• 💬 Отвечаю на вопросы\n"
        f"• 💱 Курсы валют\n"
        f"• 🔍 Поиск информации\n"
        f"• 🎙️ Голосовые сообщения\n"
        f"• 🎵 Spotify\n"
        f"• 💰 Учёт финансов\n"
        f"• 📝 Заметки в Obsidian\n\n"
        f"Финансы:\n"
        f"• потратил 500 руб на продукты\n"
        f"• получил 50000 руб зарплата\n"
        f"• бюджет на еду 5000 руб\n"
        f"• отчёт за месяц\n"
        f"• баланс\n"
        f"• копилка (автоматически 10% от доходов)\n"
        f"• положи в копилку 5000\n"
        f"• сними из копилки 3000\n\n"
        f"/reset — история, /status — статус"
    )


async def handle_reset(update, context):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        return
    session_manager.clear(user_id)
    await update.message.reply_text("🗑️ История диалога очищена.")


async def handle_status(update, context):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        return
    claude_ok = "✅" if router.claude.is_available() else "❌"
    gemini_ok = "✅" if router.gemini.is_available() else "❌"
    groq_ok = "✅" if router.groq.is_available() else "❌"
    desktop_ok = "✅" if await desktop.is_running() else "❌"
    history_info = session_manager.summary(user_id)
    await update.message.reply_text(
        f"📊 *Статус системы*\n\n"
        f"{claude_ok} Claude API\n"
        f"{gemini_ok} Gemini API\n"
        f"{groq_ok} Groq API\n"
        f"{desktop_ok} Desktop Agent\n\n"
        f"💬 История: {history_info}",
        parse_mode="Markdown"
    )
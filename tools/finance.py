from oauth2client.service_account import ServiceAccountCredentials
import gspread
import config
from datetime import datetime
import pytz

import os
import gspread
import logging
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import uuid
import re
from datetime import datetime
import pytz

TIMEZONE = pytz.timezone("Europe/Moscow")  # или твой часовой пояс

logger = logging.getLogger(__name__)

CATEGORIES = [
    "🛒 Еда и продукты", "🍽️ Кафе и рестораны", "🚕 Транспорт",
    "🏠 Жильё и коммуналки", "🎉 Развлечения", "👕 Одежда",
    "📱 Подписки", "💊 Здоровье", "✈️ Путешествия", "📚 Образование",
    "💻 Техника и гаджеты", "💇 Красота и уход", "🎁 Подарки",
    "💼 Работа и бизнес", "🔧 Ремонт и обслуживание",
    "💰 Инвестиции и сбережения", "💸 Переводы", "💵 Доход", "❓ Разное"
]

CATEGORY_KEYWORDS = {
    "🛒 Еда и продукты": ["продукты", "магазин", "супермаркет", "carrefour", "глобус", "nikora", "еда", "еду", "продукт"],
    "🍽️ Кафе и рестораны": ["кафе", "ресторан", "кофе", "coffee", "pizza", "пицца", "burger", "бургер", "суши"],
    "🚕 Транспорт": ["такси", "bolt", "uber", "яндекс", "метро", "автобус", "бензин", "парковка", "транспорт"],
    "🏠 Жильё и коммуналки": ["аренда", "квартира", "коммуналка", "свет", "вода", "газ", "интернет", "жильё", "жилье"],
    "🎉 Развлечения": ["кино", "театр", "концерт", "клуб", "бар", "игры", "netflix", "развлечения"],
    "👕 Одежда": ["одежда", "обувь", "zara", "одежду"],
    "📱 Подписки": ["подписка", "subscription", "netflix", "apple", "google", "подписки"],
    "💊 Здоровье": ["аптека", "врач", "больница", "лекарства", "pharmacy", "спорт", "gym", "здоровье"],
    "✈️ Путешествия": ["отель", "билет", "авиа", "flight", "hotel", "airbnb", "виза", "путешествия"],
    "📚 Образование": ["курс", "книга", "обучение", "школа", "университет", "udemy", "образование"],
    "💻 Техника и гаджеты": ["телефон", "ноутбук", "техника", "samsung", "электроника", "гаджет"],
    "💇 Красота и уход": ["парикмахер", "салон", "косметика", "маникюр", "beauty", "красота", "уход"],
    "🎁 Подарки": ["подарок", "gift", "праздник", "подарки"],
    "💼 Работа и бизнес": ["офис", "бизнес", "реклама", "домен", "хостинг", "работа"],
    "🔧 Ремонт и обслуживание": ["ремонт", "мастер", "запчасти", "сервис", "обслуживание"],
    "💰 Инвестиции и сбережения": ["инвестиции", "акции", "накопления", "вклад", "сбережения"],
    "💸 Переводы": ["перевод", "transfer", "отправил", "перечислил"],
    "💵 Доход": ["зарплата", "доход", "получил", "заработал", "фриланс"],
}

MONTH_NAMES = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}


def get_sheets():
    gc = gspread.service_account(filename=os.getenv("GOOGLE_CREDENTIALS_PATH"))
    sh = gc.open_by_key(os.getenv("GOOGLE_SHEETS_ID"))
    return sh


def get_current_month_str():
    """Возвращает текущий месяц в формате YYYY-MM"""
    return datetime.now().strftime("%Y-%m")


def get_txn_month(date_str):
    """Извлекает YYYY-MM из даты формата YYYY-MM-DD HH:MM"""
    return str(date_str)[:7]


def detect_category(text):
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return "❓ Разное"



async def check_budget_alert(category, new_amount_rub):
    try:
        sh = get_sheets()
        ws_budget = sh.worksheet("Budgets")
        records = ws_budget.get_all_records()
        current_month = get_current_month_str()
        for i, row in enumerate(records):
            if row.get("Категория") != category:
                continue
            budget = Decimal(str(row.get("Бюджет (RUB)", 0)))
            if budget <= 0:
                return ""
            ws_txn = sh.worksheet("Transactions")
            txn_records = ws_txn.get_all_records()
            already_spent = Decimal("0")
            for txn in txn_records:
                if not txn.get("Дата"):
                    continue
                if get_txn_month(txn["Дата"]) == current_month and txn.get("Категория") == category and txn.get("Тип") == "Расход":
                    already_spent += Decimal(str(txn.get("Сумма в RUB", 0)))
            total_spent = already_spent + new_amount_rub
            remaining = budget - total_spent
            pct = int((total_spent / budget) * 100)
            ws_budget.update_cell(i + 2, 3, float(total_spent))
            ws_budget.update_cell(i + 2, 4, float(max(remaining, Decimal("0"))))
            if pct >= 100:
                return f"\n\n⚠️ *Бюджет превышен!*\n{category}\nПотрачено: {total_spent:,.0f} ₽ из {budget:,.0f} ₽ ({pct}%)"
            elif pct >= 80:
                return f"\n\n⚠️ *Осторожно!* {pct}% бюджета использовано\n{category}: осталось {remaining:,.0f} ₽"
            return ""
        return ""
    except Exception as e:
        logger.error(f"Ошибка проверки бюджета: {e}")
        return ""


        
        # Используем переданную категорию или определённую
        final_category = category if category else detected_category
        
        match = re.search(r"(\d[\d\s]*(?:[.,]\d+)?)", text)
        if not match:
            return "❌ Не нашёл сумму. Пример: бюджет на еду 5000 руб"

        amount = Decimal(match.group(1).replace(" ", "").replace(",", "."))

        sh = get_sheets()
        ws = sh.worksheet("Budgets")
        records = ws.get_all_records()

        for i, row in enumerate(records):
            if row.get("Категория") == category:
                ws.update_cell(i + 2, 2, float(amount))
                return f"✅ Бюджет установлен!\n\n📂 {category}\n💰 Лимит: {amount:,.0f} ₽ в месяц"

        return f"❌ Категория {category} не найдена в таблице."
    except Exception as e:
        logger.error(f"Ошибка установки бюджета: {e}")
        return f"❌ Ошибка: {str(e)}"


async def get_budget_status():
    try:
        sh = get_sheets()
        ws = sh.worksheet("Budgets")
        records = ws.get_all_records()
        current_month = get_current_month_str()
        now = datetime.now(TIMEZONE)
        month_name = MONTH_NAMES[now.month]
        
        txn_ws = sh.worksheet("Transactions")
        txn_data = txn_ws.get_all_values()
        txn_records = []

        # Первая строка — это данные, не заголовки
        for row in txn_data:
            if len(row) >= 5 and row[0]:  # Проверяем что есть дата
                txn_records.append({
                    "Дата": row[0],
                    "Категория": row[2],
                    "Сумма в RUB": row[4]
                })
        
        spent_by_cat = {}
        for txn in txn_records:
            txn_date = txn.get("Дата")
            if not txn_date:
                continue
    
            txn_month = get_txn_month(txn_date)
            logger.info(f"Транзакция: {txn_date} → месяц {txn_month}, текущий {current_month}")
    
            if txn_month == current_month:
                cat = txn.get("Категория", "❓ Разное")
                amount_str = str(txn.get("Сумма в RUB", 0)).strip()
                
                try:
                    amount = Decimal(amount_str)
                    # Считаем расходы (все кроме категории "💵 Доход")
                    if cat != "💵 Доход":
                        spent_by_cat[cat] = spent_by_cat.get(cat, Decimal("0")) + abs(amount)
                except:
                    continue
        
        lines = [f"🎯 *Бюджеты на {month_name}*\n"]
        has_budgets = False
        
        for row in records:
            cat = row.get("Категория", "")
            budget_str = str(row.get("Бюджет (RUB)", 0)).strip()
            
            try:
                budget = Decimal(budget_str) if budget_str else Decimal("0")
            except:
                continue
            
            if budget <= 0 or cat in ["💵 Доход", "💸 Переводы"]:
                continue
            
            has_budgets = True
            spent = spent_by_cat.get(cat, Decimal("0"))
            remaining = budget - spent
            pct = int((spent / budget) * 100) if budget > 0 else 0
            
            if pct >= 100:
                status = f"🔴 превышен! ({pct}%)"
            elif pct >= 80:
                status = f"🟡 {pct}% — осталось {remaining:,.0f} ₽"
            else:
                status = f"🟢 {pct}% — осталось {remaining:,.0f} ₽"
            
            lines.append(f"{cat}: {spent:,.0f} / {budget:,.0f} ₽ {status}\n")
        
        if not has_budgets:
            return "📭 Бюджеты ещё не установлены.\n\nУстанови так:\n• бюджет на еду 5000 руб\n• бюджет на транспорт 3000 руб"

        # Обновляем статус в таблице
        updates = []
        all_rows = ws.get_all_values()

        for row_idx, table_row in enumerate(all_rows, start=1):
            if len(table_row) > 0:
                cat = table_row[0]
                if cat in spent_by_cat:
                    spent = spent_by_cat[cat]
                    updates.append({
                        'range': f'C{row_idx}',
                        'values': [[str(spent)]]
                    })

        if updates:
            ws.batch_update(updates)

        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Ошибка статуса бюджетов: {e}")
        return f"❌ Ошибка: {str(e)}"
        

async def get_balance():
    try:
        sh = get_sheets()
        ws = sh.worksheet("Transactions")
        records = ws.get_all_records()
        balances = {"RUB": Decimal("0"), "GEL": Decimal("0"), "USD": Decimal("0"), "EUR": Decimal("0")}
        for row in records:
            if not row.get("Тип"):
                continue
            currency = row.get("Валюта", "RUB")
            amount = Decimal(str(row.get("Сумма", 0)))
            txn_type = row.get("Тип", "")
            if currency not in balances:
                balances[currency] = Decimal("0")
            if txn_type == "Доход":
                balances[currency] += amount
            elif txn_type == "Расход":
                balances[currency] -= amount
        symbols = {"RUB": "₽", "GEL": "₾", "USD": "$", "EUR": "€"}
        lines = ["💳 *Баланс счетов*\n"]
        for currency, balance in balances.items():
            if balance == 0:
                continue
            symbol = symbols.get(currency, currency)
            sign = "+" if balance >= 0 else ""
            lines.append(f"{currency}: {sign}{balance:,.2f} {symbol}")
        if len(lines) == 1:
            return "📭 Транзакций ещё нет."
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Ошибка баланса: {e}")
        return f"❌ Ошибка: {str(e)}"

async def recalculate_budget(category):
    """Пересчитывает бюджет для категории"""
    try:
        sh = get_sheets()
        ws_budget = sh.worksheet("Budgets")
        records = ws_budget.get_all_records()
        current_month = get_current_month_str()
        
        for i, row in enumerate(records):
            if row.get("Категория") != category:
                continue
            
            budget = Decimal(str(row.get("Бюджет (RUB)", 0)))
            if budget <= 0:
                return
            
            # Считаем заново все расходы по категории за текущий месяц
            ws_txn = sh.worksheet("Transactions")
            txn_records = ws_txn.get_all_records()
            total_spent = Decimal("0")
            
            for txn in txn_records:
                if not txn.get("Дата"):
                    continue
                if (get_txn_month(txn["Дата"]) == current_month and 
                    txn.get("Категория") == category and 
                    txn.get("Тип") == "Расход"):
                    total_spent += Decimal(str(txn.get("Сумма в RUB", 0)))
            
            remaining = budget - total_spent
            
            # Обновляем бюджет
            ws_budget.update_cell(i + 2, 3, float(total_spent))
            ws_budget.update_cell(i + 2, 4, float(max(remaining, Decimal("0"))))
            return
    except Exception as e:
        logger.error(f"Ошибка пересчёта бюджета: {e}")

async def undo_last_transaction():
    try:
        sh = get_sheets()
        ws = sh.worksheet("Transactions")
        records = ws.get_all_records()
        if not records:
            return "📭 Нет транзакций для отмены."
        last = records[-1]
        last_row = len(records) + 1
        
        # Сохраняем данные для пересчёта бюджета
        category = last.get('Категория')
        txn_type = last.get('Тип')
        amount_rub = Decimal(str(last.get('Сумма в RUB', 0)))
        
        # Удаляем транзакцию
        ws.delete_rows(last_row)
        
        # Пересчитываем бюджет если это был расход
        if txn_type == "Расход" and category:
            await recalculate_budget(category)
        
        return (f"↩️ Отменена последняя транзакция:\n\n"
                f"📝 {category}\n"
                f"💰 {last.get('Сумма')} {last.get('Валюта')}\n"
                f"📅 {last.get('Дата')}\n"
                f"🆔 #{last.get('ID')}")
    except Exception as e:
        logger.error(f"Ошибка отмены: {e}")
        return f"❌ Ошибка: {str(e)}"

async def add_transaction(text, rate=1.0, parsed_data: dict = None):
    """
    Добавляет транзакцию.
    parsed_data = {"amount": 500, "category": "🚕 Транспорт", "description": "такси", "type": "expense"}
    """
    try:
        if not parsed_data:
            return "❌ Не удалось распознать транзакцию"

        amount = parsed_data.get("amount")
        category = parsed_data.get("category", "❓ Разное")
        description = parsed_data.get("description", "")
        trans_type = parsed_data.get("type", "expense")  # expense или income

        if not amount:
            return "❌ Не нашёл сумму в сообщении"

        # Конвертируем в рубли
        amount_rub = float(amount) * rate

        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_SHEETS_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(config.GOOGLE_SHEETS_ID)
        
        ws = sh.worksheet("Transactions")

        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # ID транзакции
        trans_id = len(ws.get_all_values())
        
        # Тип транзакции
        txn_type = "Доход" if trans_type == "income" else "Расход"
        
        # Валюта (пока только RUB)
        currency = "RUB"
        
        # Счёт (по умолчанию Наличные RUB)
        account = "Наличные RUB"

        # Добавляем транзакцию
        ws.append_row([
            trans_id,
            date_str,
            txn_type,
            amount,
            currency,
            amount_rub,
            category,
            account,
            description,
            rate
        ])

        # Обновляем Dashboard только для расходов
        if trans_type == "expense":
            ws_dash = sh.worksheet("Dashboard")
            all_values = ws_dash.get_all_values()
            
            # Ищем категорию и обновляем потраченную сумму
            for i, row in enumerate(all_values[7:23], start=8):
                if row and row[0] == category:
                    # Получаем текущую сумму трат
                    current_spent_str = row[2]
                    current_spent = float(current_spent_str.replace(' ₽', '').replace(',', '').replace(' ', '')) if current_spent_str and current_spent_str != '0 ₽' else 0
                    new_spent = current_spent + amount_rub
                    
                    # Обновляем колонку C (Spent)
                    ws_dash.update_acell(f'C{i}', f'{new_spent:,.0f} ₽')
                    
                    # Обновляем статус в колонке D
                    budget_str = row[1]
                    if budget_str and budget_str != '0 ₽' and budget_str != '—':
                        budget = float(budget_str.replace(' ₽', '').replace(',', '').replace(' ', ''))
                        percentage = (new_spent / budget) * 100
                        status = f"{new_spent:,.0f} ₽ ({percentage:.0f}%)"
                        ws_dash.update_acell(f'D{i}', status)
                    break

            # Обновляем Top Expenses
            expenses = {}
            total_expenses = 0
            ws_trans = sh.worksheet("Transactions")
            all_trans = ws_trans.get_all_values()
            for trans_row in all_trans[1:]:
                if trans_row[2] == "Расход":
                    cat = trans_row[6]
                    amt = float(trans_row[5])
                    expenses[cat] = expenses.get(cat, 0) + amt
                    total_expenses += amt
            
            top_expenses = sorted(expenses.items(), key=lambda x: x[1], reverse=True)[:5]
            top_data = []
            for cat, amt in top_expenses:
                pct = (amt / total_expenses * 100) if total_expenses > 0 else 0
                top_data.append([cat, amt, f'{pct:.1f}%', '—'])
            while len(top_data) < 5:
                top_data.append(['—', 0, '—', '—'])
            ws_dash.update(values=top_data, range_name='A27:D31')
        
        # Автоматически откладываем 10% от дохода в копилку
        piggy_message = ""
        if trans_type == "income":
            piggy_result = await auto_save_to_piggy_bank(amount_rub, 10.0)
            piggy_message = f"\n\n{piggy_result}"

        emoji = "💵" if trans_type == "income" else "💸"
        action = "Получено" if trans_type == "income" else "Потрачено"

        return (
            f"{emoji} {action}!\n\n"
            f"📂 {category}\n"
            f"💰 {abs(amount_rub):,.0f} ₽\n"
            f"📝 {description if description else '—'}"
            f"{piggy_message}"
        )

    except Exception as e:
        logger.error(f"Ошибка добавления транзакции: {e}")
        return f"❌ Ошибка: {str(e)}"



async def get_monthly_report():
    try:
        sh = get_sheets()
        ws = sh.worksheet("Transactions")
        records = ws.get_all_records()
        current_month = get_current_month_str()
        income = Decimal("0")
        expenses = Decimal("0")
        categories = {}
        count = 0
        for row in records:
            if not row.get("Дата"):
                continue
            if get_txn_month(row["Дата"]) != current_month:
                continue
            count += 1
            amount_rub = Decimal(str(row.get("Сумма в RUB", 0)))
            txn_type = row.get("Тип", "")
            category = row.get("Категория", "❓ Разное")
            if txn_type == "Доход":
                income += amount_rub
            else:
                expenses += amount_rub
                categories[category] = categories.get(category, Decimal("0")) + amount_rub
        balance = income - expenses
        now = datetime.now()
        month_name = f"{MONTH_NAMES[now.month]} {now.year}"
        report = (f"📊 *Отчёт за {month_name}*\n\n"
                  f"💚 Доходы: +{income:,.0f} ₽\n"
                  f"❤️ Расходы: -{expenses:,.0f} ₽\n"
                  f"{'💰' if balance >= 0 else '⚠️'} Остаток: {'+' if balance >= 0 else ''}{balance:,.0f} ₽\n"
                  f"📝 Транзакций: {count}\n\n")
        if categories:
            report += "*Топ расходов:*\n"
            top = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
            for cat, amt in top:
                report += f"  {cat}: {amt:,.0f} ₽\n"
        return report
    except Exception as e:
        logger.error(f"Ошибка отчёта: {e}", exc_info=True)
        return f"❌ Ошибка: {str(e)}"


def is_finance_command(text):
    keywords = ["потратил", "купил", "заплатил", "оплатил", "потратила", "получил", "заработал", "зарплата", "перевёл", "перевел", "трата", "расход", "доход"]
    return any(kw in text.lower() for kw in keywords)


def is_report_request(text):
    keywords = ["отчёт", "отчет", "сколько потратил", "расходы за", "доходы за", "статистика", "итого", "топ трат"]
    return any(kw in text.lower() for kw in keywords)


def is_budget_command(text):
    return "бюджет" in text.lower()


def is_balance_request(text):
    keywords = ["баланс", "сколько денег", "сколько у меня", "мои деньги", "остаток на счёте"]
    return any(kw in text.lower() for kw in keywords)


def is_undo_request(text):
    text_lower = text.lower()
    # Исключаем команды удаления бюджета
    if is_remove_budget_request(text_lower):
        return False
    keywords = ["отмени последнюю", "отменить последнюю", "удали последнюю", "undo", "ошибся"]
    return any(kw in text_lower for kw in keywords)


def is_remove_budget_request(text):
    keywords = ["удали бюджет", "отмени бюджет", "убери бюджет", "сбрось бюджет"]
    return any(kw in text.lower() for kw in keywords)




async def update_budget_status(category: str, spent_amount: float):
    """Обновляет статус бюджета в Dashboard после добавления траты"""
    try:
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_SHEETS_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(config.GOOGLE_SHEETS_ID)
        
        ws = sh.worksheet("Dashboard")
        all_values = ws.get_all_values()
        
        # Ищем категорию
        for i, row in enumerate(all_values[7:23], start=8):
            if row and row[0] == category:
                # Обновляем потраченную сумму в колонке C
                ws.update_acell(f'C{i}', f'{spent_amount:,.0f} ₽')
                
                # Получаем бюджет из колонки B
                budget_str = row[1]
                if budget_str and budget_str != '0 ₽' and budget_str != '—':
                    budget = float(budget_str.replace(' ₽', '').replace(',', '').replace(' ', ''))
                    percentage = (spent_amount / budget) * 100
                    status = f"{spent_amount:,.0f} ₽ ({percentage:.0f}%)"
                    ws.update_acell(f'D{i}', status)
                break
                
    except Exception as e:
        logger.error(f"Ошибка update_budget_status: {e}")


async def set_budget(text, category: str = None):
    """Устанавливает бюджет для категории в Dashboard"""
    try:
        # Извлекаем сумму из текста
        match = re.search(r"(\d[\d\s]*(?:[.,]\d+)?)", text)
        if not match:
            return "❌ Не нашёл сумму. Пример: бюджет на еду 5000"

        amount = float(match.group(1).replace(" ", "").replace(",", "."))

        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_SHEETS_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(config.GOOGLE_SHEETS_ID)
        
        ws = sh.worksheet("Dashboard")
        all_values = ws.get_all_values()
        
        # Ищем категорию в Dashboard (строки 8-23)
        category_row = None
        for i, row in enumerate(all_values[7:23], start=8):  # строки с категориями
            if row and row[0] == category:
                category_row = i
                break
        
        if not category_row:
            return f"❌ Категория '{category}' не найдена в Dashboard"
        
        # Обновляем бюджет в колонке B
        ws.update_acell(f'B{category_row}', f'{amount:,.0f} ₽')
        
        # Получаем текущие траты из колонки C
        spent_str = all_values[category_row - 1][2]
        spent = float(spent_str.replace(' ₽', '').replace(',', '').replace(' ', '')) if spent_str and spent_str != '0 ₽' else 0
        
        # Обновляем статус в колонке D
        if amount > 0:
            percentage = (spent / amount) * 100
            status = f"{spent:,.0f} ₽ ({percentage:.0f}%)"
        else:
            status = "—"
        
        ws.update_acell(f'D{category_row}', status)
        
        return f"✅ Бюджет установлен!\n\n📂 {category}\n💰 Лимит: {amount:,.0f} ₽ в месяц"
        
    except Exception as e:
        logger.error(f"Ошибка set_budget: {e}", exc_info=True)
        return f"❌ Ошибка: {e}"


async def remove_budget(text, category: str = None):
    """Удаляет бюджет категории. category передаётся из handlers.py через AI."""
    try:
        sh = get_sheets()
        ws = sh.worksheet("Budgets")
        records = ws.get_all_records()

        for i, row in enumerate(records):
            if row.get("Категория") == category:
                ws.update_cell(i + 2, 2, 0)
                return f"✅ Бюджет на {category} удалён!"

        return f"❌ Категория {category} не найдена в таблице."
    except Exception as e:
        logger.error(f"Ошибка удаления бюджета: {e}")
        return f"❌ Ошибка: {str(e)}"

def is_remove_budget_request(text):
    keywords = ["удали бюджет", "отмени бюджет", "убери бюджет", "сбрось бюджет"]
    return any(kw in text.lower() for kw in keywords)



def is_remove_budget_request(text):
    keywords = ["удали бюджет", "отмени бюджет", "убери бюджет", "сбрось бюджет"]
    return any(kw in text.lower() for kw in keywords)
def _update_budget_in_sheet(category: str, amount: float) -> str:
    try:
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_SHEETS_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(config.GOOGLE_SHEETS_ID)

        ws = sh.worksheet("Dashboard")
        categories = ws.col_values(1)[3:]  # начиная с A4

        simple_map = {
            'еда': '🛒 Еда и продукты',
            'транспорт': '🚕 Транспорт',
            'жилье': '🏠 Жильё и коммуналки',
            'развлечения': '🎉 Развлечения',
            'одежда': '👕 Одежда',
            'подписки': '📱 Подписки',
            'здоровье': '💊 Здоровье',
            'путешествия': '✈️ Путешествия',
            'образование': '📚 Образование',
            'техника': '💻 Техника и гаджеты',
            'красота': '💇 Красота и уход',
            'подарки': '🎁 Подарки',
            'работа': '💼 Работа и бизнес',
            'ремонт': '🔧 Ремонт и обслуживание',
            'инвестиции': '💰 Инвестиции и сбережения',
            'разное': '❓ Разное',
        }

        key = category.strip().lower()
        full_category = simple_map.get(key)
        if not full_category:
            for k, v in simple_map.items():
                if key in k:
                    full_category = v
                    break

        if not full_category:
            available = ', '.join(simple_map.keys())
            return f"❌ Неизвестная категория. Доступные: {available}"

        if full_category not in categories:
            return f"❌ Категория '{full_category}' не найдена в таблице"

        row_idx = categories.index(full_category) + 4  # строка с учётом A4

        ws.update_acell(f'B{row_idx}', amount)

        return f"✅ Бюджет для {full_category} установлен на {amount:,.0f} ₽"

    except Exception as e:
        return f"❌ Ошибка при установке бюджета: {e}"

async def clear_all_budgets(text):
    """Обнуляет все бюджеты"""
    try:
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_SHEETS_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(config.GOOGLE_SHEETS_ID)
        
        ws = sh.worksheet("Dashboard")
        
        # Обнуляем бюджеты начиная с B4 (где начинаются категории)
        categories = ws.col_values(1)[3:]  # начиная с A4
        
        for i, cat in enumerate(categories):
            if cat and cat.strip():  # если категория не пустая
                row_idx = i + 4  # +4 потому что начинаем с A4
                ws.update_acell(f'B{row_idx}', 0)
        
        return "✅ Все бюджеты обнулены"
        
    except Exception as e:
        return f"❌ Ошибка при обнулении бюджетов: {e}"


if __name__ == "__main__":
    # тест примера
    print(set_budget("Еда", 30000))


# ============= КОПИЛКА =============

async def get_piggy_bank_balance():
    """Получить баланс копилки"""
    try:
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_SHEETS_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(config.GOOGLE_SHEETS_ID)
        
        ws = sh.worksheet("Accounts")
        all_values = ws.get_all_values()
        
        for row in all_values[1:]:
            if row and row[0] == "🐷 Копилка":
                balance = float(row[2]) if row[2] else 0
                return f"🐷 Копилка: {balance:,.0f} ₽"
        
        return "🐷 Копилка: 0 ₽ (счёт не создан)"
        
    except Exception as e:
        return f"❌ Ошибка: {e}"


async def add_to_piggy_bank(amount: float, description: str = "Пополнение копилки"):
    """Добавить деньги в копилку"""
    try:
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_SHEETS_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(config.GOOGLE_SHEETS_ID)
        
        ws_accounts = sh.worksheet("Accounts")
        all_values = ws_accounts.get_all_values()
        
        piggy_row = None
        for i, row in enumerate(all_values[1:], start=2):
            if row and row[0] == "🐷 Копилка":
                piggy_row = i
                break
        
        if not piggy_row:
            piggy_row = len(all_values) + 1
            ws_accounts.append_row(["🐷 Копилка", "RUB", amount, amount])
        else:
            current_balance = float(all_values[piggy_row - 1][2]) if all_values[piggy_row - 1][2] else 0
            new_balance = current_balance + amount
            ws_accounts.update_acell(f'C{piggy_row}', new_balance)
            ws_accounts.update_acell(f'D{piggy_row}', new_balance)
        
        ws_trans = sh.worksheet("Transactions")
        from datetime import datetime
        trans_id = len(ws_trans.get_all_values())
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        ws_trans.append_row([
            trans_id,
            date_str,
            "Копилка",
            amount,
            "RUB",
            amount,
            "💰 Копилка",
            "🐷 Копилка",
            description,
            1.0
        ])
        
        return f"✅ Добавлено в копилку: {amount:,.0f} ₽\n💬 {description}"
        
    except Exception as e:
        return f"❌ Ошибка: {e}"


async def withdraw_from_piggy_bank(amount: float, description: str = "Снятие из копилки"):
    """Снять деньги из копилки"""
    try:
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_SHEETS_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(config.GOOGLE_SHEETS_ID)
        
        ws_accounts = sh.worksheet("Accounts")
        all_values = ws_accounts.get_all_values()
        
        piggy_row = None
        for i, row in enumerate(all_values[1:], start=2):
            if row and row[0] == "🐷 Копилка":
                piggy_row = i
                break
        
        if not piggy_row:
            return "❌ Копилка не найдена"
        
        current_balance = float(all_values[piggy_row - 1][2]) if all_values[piggy_row - 1][2] else 0
        
        if current_balance < amount:
            return f"❌ Недостаточно средств в копилке. Доступно: {current_balance:,.0f} ₽"
        
        new_balance = current_balance - amount
        ws_accounts.update_acell(f'C{piggy_row}', new_balance)
        ws_accounts.update_acell(f'D{piggy_row}', new_balance)
        
        ws_trans = sh.worksheet("Transactions")
        from datetime import datetime
        trans_id = len(ws_trans.get_all_values())
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        ws_trans.append_row([
            trans_id,
            date_str,
            "Снятие",
            -amount,
            "RUB",
            -amount,
            "💰 Копилка",
            "🐷 Копилка",
            description,
            1.0
        ])
        
        return f"✅ Снято из копилки: {amount:,.0f} ₽\n💰 Остаток: {new_balance:,.0f} ₽\n💬 {description}"
        
    except Exception as e:
        return f"❌ Ошибка: {e}"




async def update_dashboard_summary(sh):
    """Обновляет сводку Income/Expenses/Balance на Dashboard"""
    ws_dash = sh.worksheet("Dashboard")
    ws_trans = sh.worksheet("Transactions")
    
    # Считаем значения
    all_trans = ws_trans.get_all_values()
    total_income = 0
    total_expenses = 0
    trans_count = 0
    
    for row in all_trans[1:]:
        if len(row) > 5:
            trans_type = row[2]
            amount_rub = float(row[5]) if row[5] else 0
            
            if trans_type == "Доход":
                total_income += amount_rub
            elif trans_type == "Расход":
                total_expenses += amount_rub
            
            trans_count += 1
    
    balance = total_income - total_expenses
    
    # Обновляем строку 4
    ws_dash.update(values=[[
        f'{total_income:,.0f} ₽',
        f'{total_expenses:,.0f} ₽',
        f'{balance:,.0f} ₽',
        str(trans_count)
    ]], range_name='A4:D4')

async def auto_save_to_piggy_bank(income_amount: float, percentage: float = 10.0):
    """Автоматически откладывает процент от дохода в копилку"""
    save_amount = income_amount * (percentage / 100)
    return await add_to_piggy_bank(save_amount, f"Автоматическое откладывание {percentage}% от дохода {income_amount:,.0f} ₽")



async def compare_with_previous_month():
    """Сравнивает траты текущего месяца с прошлым по категориям"""
    try:
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_SHEETS_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(config.GOOGLE_SHEETS_ID)
        
        ws = sh.worksheet("Transactions")
        all_trans = ws.get_all_values()
        
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        now = datetime.now()
        current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month = current_month - relativedelta(months=1)
        
        # Собираем траты по категориям за два месяца
        current_expenses = {}
        previous_expenses = {}
        
        for row in all_trans[1:]:
            if row[2] == "Расход":
                date_str = row[1]
                trans_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                category = row[6]
                amount = float(row[5])
                
                if trans_date >= current_month:
                    current_expenses[category] = current_expenses.get(category, 0) + amount
                elif trans_date >= previous_month and trans_date < current_month:
                    previous_expenses[category] = previous_expenses.get(category, 0) + amount
        
        # Все уникальные категории
        all_categories = set(list(current_expenses.keys()) + list(previous_expenses.keys()))
        
        # Формируем отчёт
        result = f"📊 Сравнение с прошлым месяцем\n\n"
        result += f"📅 {previous_month.strftime('%B %Y')} vs {current_month.strftime('%B %Y')}\n\n"
        
        comparisons = []
        for category in all_categories:
            current = current_expenses.get(category, 0)
            previous = previous_expenses.get(category, 0)
            
            if previous > 0:
                diff = current - previous
                diff_percent = (diff / previous) * 100
                
                if diff > 0:
                    trend = "📈"
                    sign = "+"
                elif diff < 0:
                    trend = "📉"
                    sign = ""
                else:
                    trend = "➡️"
                    sign = ""
                
                comparisons.append({
                    'category': category,
                    'current': current,
                    'previous': previous,
                    'diff': diff,
                    'diff_percent': diff_percent,
                    'trend': trend,
                    'sign': sign
                })
            elif current > 0:
                # Новая категория в этом месяце
                comparisons.append({
                    'category': category,
                    'current': current,
                    'previous': 0,
                    'diff': current,
                    'diff_percent': 0,
                    'trend': "🆕",
                    'sign': "+"
                })
        
        # Сортируем по абсолютной разнице
        comparisons.sort(key=lambda x: abs(x['diff']), reverse=True)
        
        for comp in comparisons:
            result += f"{comp['trend']} {comp['category']}\n"
            result += f"   Сейчас: {comp['current']:,.0f} ₽\n"
            result += f"   Было: {comp['previous']:,.0f} ₽\n"
            
            if comp['diff_percent'] != 0:
                result += f"   Разница: {comp['sign']}{comp['diff']:,.0f} ₽ ({comp['sign']}{comp['diff_percent']:.0f}%)\n"
            else:
                result += f"   Разница: {comp['sign']}{comp['diff']:,.0f} ₽ (новая категория)\n"
            result += "\n"
        
        # Итоговая статистика
        total_current = sum(current_expenses.values())
        total_previous = sum(previous_expenses.values())
        total_diff = total_current - total_previous
        
        if total_previous > 0:
            total_diff_percent = (total_diff / total_previous) * 100
            result += f"━━━━━━━━━━━━━━━━━━━━\n"
            result += f"💰 Итого:\n"
            result += f"   Сейчас: {total_current:,.0f} ₽\n"
            result += f"   Было: {total_previous:,.0f} ₽\n"
            
            if total_diff > 0:
                result += f"   📈 +{total_diff:,.0f} ₽ (+{total_diff_percent:.0f}%)"
            elif total_diff < 0:
                result += f"   📉 {total_diff:,.0f} ₽ ({total_diff_percent:.0f}%)"
            else:
                result += f"   ➡️ Без изменений"
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка сравнения с прошлым месяцем: {e}")
        return f"❌ Ошибка: {str(e)}"

import httpx
import os
from datetime import datetime

API_KEY = os.getenv("EXCHANGERATE_API_KEY", "")
BASE_URL = "https://api.exchangerate.host"


async def get_rates(base: str = "USD", symbols: list = None) -> dict:
    try:
        params = {"access_key": API_KEY, "source": base.upper()}
        if symbols:
            params["currencies"] = ",".join(s.upper() for s in symbols)

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{BASE_URL}/live", params=params)
            data = resp.json()

        if not data.get("success"):
            return {}

        # Конвертируем USDGEL → GEL: value
        quotes = data.get("quotes", {})
        result = {}
        for key, value in quotes.items():
            target = key[len(base):]  # убираем базовую валюту из начала
            result[target] = value

        return result

    except Exception as e:
        return {}


async def format_currency_info(query: str) -> str:
    query_lower = query.lower()
    today = datetime.now().strftime("%d.%m.%Y")

    currency_map = {
        "доллар": "USD", "dollar": "USD", "usd": "USD",
        "евро": "EUR", "euro": "EUR", "eur": "EUR",
        "рубль": "RUB", "ruble": "RUB", "rub": "RUB",
        "лари": "GEL", "lari": "GEL", "gel": "GEL",
        "фунт": "GBP", "pound": "GBP", "gbp": "GBP",
        "лира": "TRY", "lira": "TRY", "try": "TRY",
        "гривна": "UAH", "hryvnia": "UAH", "uah": "UAH",
    }

    found = []
    for word, code in currency_map.items():
        if word in query_lower and code not in found:
            found.append(code)

    # Базовая валюта
    base = "USD"
    if found:
        base = found[0]

    # Целевые валюты
    if any(w in query_lower for w in ["грузи", "тбилис", "georgia", "tbilisi", "лари", "gel"]):
        targets = ["GEL", "EUR", "GBP", "RUB", "TRY"]
        base = "USD"
    elif len(found) >= 2:
        base = found[0]
        targets = found[1:]
    else:
        targets = ["EUR", "GEL", "GBP", "RUB", "TRY", "UAH"]

    rates = await get_rates(base, targets)

    if not rates:
        return "Не удалось получить курсы валют."

    lines = [f"💱 Курсы валют на {today}\n"]
    for target, value in rates.items():
        if target in targets:
            lines.append(f"  1 {base} = {value:.4f} {target}")

    lines.append(f"\n📊 Источник: exchangerate.host")
    lines.append("⚠️ Курс в обменниках может отличаться на 1-3%")

    return "\n".join(lines)


def is_currency_query(text: str) -> bool:
    keywords = [
        "курс", "валют", "обмен", "доллар", "евро", "рубль", "лари",
        "фунт", "лира", "гривна", "currency", "exchange",
        "usd", "eur", "gel", "rub", "gbp", "try", "uah"
    ]
    return any(kw in text.lower() for kw in keywords)

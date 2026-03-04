from tavily import TavilyClient
import httpx
from bs4 import BeautifulSoup
import os
from datetime import datetime

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))


async def fetch_nbg_rates() -> str:
    """Официальный курс НБГ через API."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        async with httpx.AsyncClient(timeout=10) as c:
            resp = await c.get(
                f"https://nbg.gov.ge/gw/api/ct/monetarypolicy/currencies/en/json/?date={today}"
            )
            data = resp.json()
            main = ["USD", "EUR", "RUB", "GBP", "TRY", "UAH"]
            lines = ["Нацбанк Грузии (nbg.gov.ge):"]
            for item in data[0].get("currencies", []):
                if item["code"] in main:
                    lines.append(f"  {item['code']}: {item['rate']} GEL")
            return "\n".join(lines)
    except:
        return ""


async def multi_search(query: str) -> str:
    """
    Делаем 3 независимых поиска по разным запросам,
    собираем все результаты и отдаём AI для сверки.
    """
    today = datetime.now().strftime("%d.%m.%Y")
    all_results = [f"Дата запроса: {today}\n"]

    # Три разных поисковых запроса для перекрёстной проверки
    queries = [
        f"{query} {today}",
        f"{query} актуально сейчас",
        f"{query} последние данные",
    ]

    seen_urls = set()
    source_num = 1

    for q in queries:
        try:
            resp = client.search(
                query=q,
                max_results=3,
                include_answer=False,
                search_depth="advanced"
            )
            for r in resp.get("results", []):
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    pub = f" [{r['published_date']}]" if r.get("published_date") else ""
                    all_results.append(
                        f"Источник {source_num}{pub}: {r['title']}\n"
                        f"URL: {r['url']}\n"
                        f"Данные: {r['content']}\n"
                    )
                    source_num += 1
        except:
            continue

    return "\n".join(all_results)


async def web_search(query: str, max_results: int = 5) -> str:
    """Основная функция поиска с перекрёстной проверкой."""
    today = datetime.now().strftime("%d.%m.%Y")
    results = []

    # Для валют добавляем официальный НБГ
    query_lower = query.lower()
    is_currency = any(w in query_lower for w in [
        "курс", "валют", "доллар", "евро", "рубль", "обмен", "lari", "gel"
    ])

    if is_currency:
        nbg = await fetch_nbg_rates()
        if nbg:
            results.append(nbg)

    # Перекрёстный поиск по нескольким запросам
    search_data = await multi_search(query)
    results.append(search_data)

    return "\n\n".join(results)


def should_search(text: str) -> bool:
    keywords = [
        "найди", "найти", "поищи", "поиск", "актуальн", "сегодня", "сейчас",
        "текущ", "последн", "новост", "курс", "цена", "погода", "расписание",
        "где", "когда", "как добраться", "адрес", "телефон", "сайт",
        "search", "find", "latest", "current", "today", "now", "price"
    ]
    return any(kw in text.lower() for kw in keywords)

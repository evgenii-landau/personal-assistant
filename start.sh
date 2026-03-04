#!/bin/bash
# ============================================================
# start.sh — Запуск всех компонентов ассистента
# ============================================================

set -e

cd "$(dirname "$0")"

echo "🚀 Запуск Personal AI Assistant..."

# Проверяем .env
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден! Скопируй .env.example → .env и заполни его."
    exit 1
fi

# Проверяем виртуальное окружение
if [ ! -d "venv" ]; then
    echo "📦 Создаю виртуальное окружение..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📦 Устанавливаю зависимости..."
pip install -q -r requirements.txt

echo ""
echo "🖥️  Запускаю Desktop Agent (порт 8001)..."
PYTHONPATH=. python desktop_agent/server.py &
DESKTOP_PID=$!

sleep 2

echo "🤖 Запускаю Telegram Bot..."
PYTHONPATH=. python bot/main.py &
BOT_PID=$!

echo ""
echo "✅ Всё запущено!"
echo "   Desktop Agent PID: $DESKTOP_PID"
echo "   Bot PID: $BOT_PID"
echo ""
echo "Для остановки нажми Ctrl+C"

# Ждём сигнала остановки
trap "echo '🛑 Останавливаю...'; kill $DESKTOP_PID $BOT_PID 2>/dev/null; exit 0" INT TERM
wait

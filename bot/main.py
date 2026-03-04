import logging
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, filters

import config
from bot.handlers import handle_message, handle_voice, handle_start, handle_reset, handle_status

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("assistant.log"),
    ]
)
logger = logging.getLogger(__name__)


def main():
    # Проверяем конфигурацию
    errors = config.validate_config()
    if errors:
        for error in errors:
            logger.error(f"Ошибка конфигурации: {error}")
        sys.exit(1)

    logger.info("🚀 Запуск персонального AI-ассистента...")

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Регистрируем обработчики команд
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("reset", handle_reset))
    app.add_handler(CommandHandler("status", handle_status))

    # Обработчик всех текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logger.info("✅ Бот запущен. Ожидаю сообщений...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

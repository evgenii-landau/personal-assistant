
@bot.message_handler(commands=['set_budget'])
def set_budget_command(message):
    """Установить бюджет для категории"""
    try:
        # Убираем команду /set_budget
        text = message.text.replace('/set_budget', '').strip()
        
        # Разбиваем на слова
        parts = text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Использование: /set_budget <категория> <сумма>\nПример: /set_budget еда 30000")
            return
        
        # Последнее слово - это сумма, всё остальное - категория
        amount_str = parts[-1]
        category = ' '.join(parts[:-1])
        
        amount = float(amount_str.replace(',', '').replace(' ', ''))
        
        # Формируем текст для async функции
        import asyncio
        text = f"{category} {amount}"
        result = asyncio.run(finance_tools.set_budget(text))
        bot.reply_to(message, result)
        
    except ValueError:
        bot.reply_to(message, "❌ Неверный формат суммы")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

def set_budget_command(message):
    """Установить бюджет для категории"""
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "Использование: /set_budget <категория> <сумма>\nПример: /set_budget Еда 30000")
            return
        
        category = parts[1]
        amount = float(parts[2].replace(',', '').replace(' ', ''))
        
        # Формируем текст для async функции
        import asyncio
        text = f"{category} {amount}"
        result = asyncio.run(finance_tools.set_budget(text))
        bot.reply_to(message, result)
        
    except ValueError:
        bot.reply_to(message, "❌ Неверный формат суммы")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")


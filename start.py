import logging
import config
from trading import main_trading_loop
from exchange import exchange_start

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("bot_history.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('trading_bot')

if __name__ == "__main__":
    try:
        logger.info("🚀 Бот запущен и начинает работу...")

        # Инициализируем биржу
        exchange = exchange_start()

        if exchange is None:
            logger.error("❌ Не удалось подключиться к бирже!")
            exit(1)

        # Загружаем рынки
        markets = exchange.load_markets()
        market = exchange.market(config.SYMBOL)
        min_amount = market['limits']['amount']['min']
        logger.info(f"Минимальный лот для {config.SYMBOL}: {min_amount}")

        # Проверяем лот
        amount = config.AMOUNT
        if amount < min_amount:
            logger.warning(
                f"⚠️ Твой лот {amount} меньше минимума {min_amount}. "
                f"Используем минимум."
            )
            amount = min_amount

        # Запускаем торговый цикл
        main_trading_loop(exchange)

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        exit(1)
import logging
import config
from trading import main_trading_loop
from exchange import exchange_start

# Настройка логирования с DEBUG уровнем для детального просмотра
logging.basicConfig(
    level=logging.DEBUG,  # Изменено с INFO на DEBUG для видимости всех операций
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("bot_history.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('trading_bot')

# Отключаем чрезмерно подробные логи от библиотек
logging.getLogger('ccxt').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

if __name__ == "__main__":
    try:
        logger.info("🚀 Бот запущен и начинает работу...")

        # Инициализируем биржу
        exchange = exchange_start()

        if exchange is None:
            logger.error("❌ Не удалось подключиться к бирже!")
            exit(1)

        # Загружаем рынки
        logger.debug("📚 Загружаем информацию о рынках...")
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
        logger.info("=" * 60)
        logger.info("ЗАПУСК ОСНОВНОГО ТОРГОВОГО ЦИКЛА")
        logger.info("=" * 60)
        main_trading_loop(exchange)

    except KeyboardInterrupt:
        logger.info("⏹️ ПОЛУЧЕНА КОМАНДА ВЫКЛЮЧЕНИЯ")
        exit(0)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        exit(1)
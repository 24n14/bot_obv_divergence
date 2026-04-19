import logging
import config
symbol = config.SYMBOL
logger = logging.getLogger(__name__)

def has_open_position(exchange, symbol):
    """Проверяет открытую позицию (ПРАВИЛЬНО для Bybit)"""
    try:
        logger.info(f"🔍 Начинаем проверку позиции для {symbol}...")
        positions = exchange.fetch_positions()

        for pos in positions:
            if pos['symbol'] == symbol:
                # ✅ Проверяем по 'contracts' (размер позиции)
                if pos.get('contracts') and pos['contracts'] != 0:
                    logger.info(f"✅ Открыта {pos['side'].upper()}: {pos['contracts']} контрактов")
                    return True, pos

        return False, None

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False, None
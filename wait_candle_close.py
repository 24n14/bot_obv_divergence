import logging
#import datetime
import time
#import pytz
#import math

logger = logging.getLogger(__name__)

def get_timeframe_seconds(tf):
    """Конвертирует таймфрейм в секунды"""
    mapping = {
        '1m': 60, '5m': 300, '15m': 900, '30m': 1800,
        '1h': 3600, '4h': 14400, '1d': 86400
    }
    return mapping.get(tf, 300)

def wait_for_candle_close(exchange, symbol, timeframe):
    """Ждет закрытия свечи, синхронизируясь с биржей"""
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Получаем данные с синхронизацией времени биржи
            candles = exchange.fetch_ohlcv(symbol, timeframe, limit=1)
            exchange_time_ms = exchange.fetch_time()

            if not candles:
                raise ValueError("Пустой список свечей")

            candle_open_time = candles[0][0] / 1000
            timeframe_sec = get_timeframe_seconds(timeframe)
            candle_close_time = candle_open_time + timeframe_sec

            # Используем время биржи, а не локальное
            exchange_time_sec = exchange_time_ms / 1000
            wait_time = candle_close_time - exchange_time_sec

            if wait_time > 1:
                logger.info(f"⏳ Ожидание {wait_time:.1f} сек до закрытия свечи {timeframe}")
                time.sleep(wait_time + 0.5)
            elif wait_time > -60:
                logger.info(f"⏳ Свеча закроется скоро, ожидаем {max(wait_time, 0):.1f} сек")
                time.sleep(max(wait_time + 0.5, 0.5))
            else:
                logger.warning(f"⚠️ Свеча закрыта {abs(wait_time):.1f} сек назад, ждём следующую")
                next_wait = timeframe_sec + wait_time
                time.sleep(max(next_wait, 1))

            return True

        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Ошибка (попытка {retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                time.sleep(2)
            else:
                logger.error(f"❌ Не удалось синхронизироваться после {max_retries} попыток")
                return False
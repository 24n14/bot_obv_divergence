import logging
import config
import pandas as pd
import time
import numpy as np
from wait_candle_close import wait_for_candle_close
from find_obv_divergence import find_obv_divergence
from open_pos import execute_trade
from check_pos import has_open_position

logger = logging.getLogger(__name__)
symbol = config.SYMBOL
amount = config.AMOUNT


def main_trading_loop(exchange):
    logger.info("🚀 Запуск торгового бота")

    # Параметры фильтрации сигналов
    MIN_CONFIDENCE = 0.5  # минимальная уверенность для входа

    try:
        while True:
            try:
                # 1. Ждём закрытия текущей свечи
                wait_success = wait_for_candle_close(exchange, config.SYMBOL, config.TIMEFRAME)
                if not wait_success:
                    logger.warning("⚠️ Ошибка синхронизации свечи, пропускаем итерацию")
                    time.sleep(5)
                    continue

                # 2. Получаем данные (свеча уже закрыта)
                logger.debug("📥 Загружаем OHLCV данные...")
                candles = exchange.fetch_ohlcv(
                    config.SYMBOL,
                    config.TIMEFRAME,
                    limit=config.LIMIT
                )

                if not candles or len(candles) < 100:
                    logger.warning(f"⚠️ Недостаточно свечей: {len(candles) if candles else 0}")
                    time.sleep(1)
                    continue

                # 3. Создаём DataFrame
                data = pd.DataFrame(
                    candles,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )

                # 4. Конвертируем в numpy массивы
                high = data['high'].values
                low = data['low'].values
                close = data['close'].values
                volume = data['volume'].values

                # 5. Проверяем на NaN
                if np.any(np.isnan(close)) or np.any(np.isnan(volume)):
                    logger.warning("⚠️ Обнаружены NaN значения в данных")
                    time.sleep(1)
                    continue

                logger.debug(f"📊 Данные загружены: {len(close)} свечей, последняя цена: {close[-1]:.2f}")

                # 6. Генерируем сигнал
                logger.debug("🔬 Анализируем дивергенцию...")
                signal, confidence, details = find_obv_divergence(
                    high, low, close, volume, lookback=50
                )

                logger.debug(f"Результат анализа: signal={signal}, confidence={confidence:.2%}")

                # 7. Проверяем наличие позиций
                has_pos, pos_data = has_open_position(exchange, config.SYMBOL)

                # 8. Логика входа с учётом confidence
                if not has_pos:
                    if signal is not None:
                        logger.info(f"📊 Сигнал: {signal.upper()}, Уверенность: {confidence:.2%}")
                        logger.info(f"   Детали: {details}")

                        if confidence >= MIN_CONFIDENCE:
                            if signal == 'bullish':
                                logger.info(f"🟢 ВХОД В LONG (confidence: {confidence:.2%})")
                                execute_trade(exchange, symbol, 'buy', amount)
                            elif signal == 'bearish':
                                logger.info(f"🔴 ВХОД В SHORT (confidence: {confidence:.2%})")
                                execute_trade(exchange, symbol, 'sell', amount)
                        else:
                            logger.info(f"⚠️ Сигнал отфильтрован (confidence {confidence:.2%} < {MIN_CONFIDENCE})")
                    else:
                        logger.debug("📭 Сигнала нет")

                elif has_pos:
                    # Опционально: логика выхода по обратному сигналу
                    if signal is not None and confidence >= 0.7:  # высокий порог для разворота
                        if (signal == 'bearish' and pos_data['side'] == 'long') or \
                                (signal == 'bullish' and pos_data['side'] == 'short'):
                            logger.info(f"🔄 Обнаружен сигнал разворота (confidence: {confidence:.2%})")
                            # Здесь логика закрытия и открытия противоположной позиции
                    else:
                        logger.debug(f"⌛ Позиция открыта ({pos_data['side'].upper()}), ожидаем...")

                # Небольшая пауза перед следующим циклом
                time.sleep(1)

            except KeyboardInterrupt:
                raise  # Пробрасываем наружу для обработки
            except Exception as e:
                logger.error(f"❌ Ошибка в торговом цикле: {e}", exc_info=True)
                time.sleep(10)

    except KeyboardInterrupt:
        logger.info("⏹️ ПОЛУЧЕНА КОМАНДА ВЫКЛЮЧЕНИЯ (Ctrl+C)")
        logger.info("✅ Позиция остаётся открытой со стоп-лоссом и тейк-профитом")
        logger.info("👋 Бот выключается...")
        return

    except Exception as e:
        logger.error(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
        raise
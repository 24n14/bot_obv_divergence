import logging
import config
import time
from pybit.unified_trading import HTTP

logger = logging.getLogger(__name__)

# === Инициализация Pybit ===
if config.DEMO_TRADING:
    session_bybit = HTTP(
        demo=True,
        api_key=config.API_KEY,
        api_secret=config.SECRET_KEY
    )
    logger.info("🧪 ДЕМО-РЕЖИМ АКТИВИРОВАН (Pybit)")
else:
    session_bybit = HTTP(
        api_key=config.API_KEY,
        api_secret=config.SECRET_KEY
    )
    logger.info("🚀 РЕАЛЬНАЯ ТОРГОВЛЯ (Pybit)")


def execute_trade(exchange, symbol, side):
    """Открытие позиции с TP/SL и трейлинг-стопом"""
    logger.info("🚀 Запуск модуля открытия позиции")

    try:
        # === 1. Проверка баланса ===
        balance_data = exchange.fetch_balance()
        currency = 'USDC' if 'USDC' in symbol else 'USDT'
        balance_before = balance_data[currency]['free']

        logger.info(f"💰 Свободный баланс: {balance_before:.2f} {currency}")

        if balance_before < config.MIN_AMOUNT:
            logger.warning(f"❌ Недостаточно средств: {balance_before:.2f} < {config.MIN_AMOUNT}")
            return False

        # === 2. Получение рыночных данных ===
        market = exchange.market(symbol)
        ticker = exchange.fetch_ticker(symbol)
        entry_price = ticker['last']
        amount = config.AMOUNT

        # Проверка минимальной стоимости
        min_cost = market.get('limits', {}).get('cost', {}).get('min')
        if min_cost is None:
            logger.warning(f"⚠️ Минимальная стоимость не определена для {symbol}")
            min_cost = 10

        if amount * entry_price < min_cost:
            logger.error(f"❌ Сумма {amount * entry_price:.2f} < минимум {min_cost}")
            return False

        # === 3. Расчет цен ===
        sl_percent = config.STOP_LOSS
        tp_percent = config.TAKE_PROFIT
        tpsl_size = config.TPSL_SIZE

        if side == 'buy':
            stop_loss_price = entry_price * (1 - sl_percent/100)
            take_profit_price = entry_price * (1 + tp_percent/100)
            ts_trigger_price = take_profit_price
        else:
            stop_loss_price = entry_price * (1 + sl_percent/100)
            take_profit_price = entry_price * (1 - tp_percent/100)
            ts_trigger_price = take_profit_price

        logger.info(f"📊 Расчетные цены:")
        logger.info(f"   Вход: {entry_price:.2f}")
        logger.info(f"   SL: {stop_loss_price:.2f} | TP: {take_profit_price:.2f}")
        logger.info(f"   TS Trigger: {ts_trigger_price:.2f}")

        # === 4. Открытие позиции через CCXT ===
        order = exchange.create_order(
            symbol,
            'Market',
            side,
            amount,
            params={
                'stopLoss': {
                    'triggerPrice': stop_loss_price,
                    'slSize': tpsl_size
                },
                'takeProfit': {
                    'triggerPrice': take_profit_price,
                    'tpSize': tpsl_size
                },
                'tpslMode': 'Partial',
                'tpOrderType': 'Market',
                'slOrderType': 'Market',
            }
        )

        logger.info(f"✅ Позиция открыта! ID: {order['id']}")
        logger.info(f"📈 {side.upper()} {amount} {symbol} @ {entry_price:.2f}")

        # === 5. Установка трейлинг-стопа через Pybit ===
        time.sleep(0.5)

        try:
            bybit_symbol = symbol.replace('/', '').split(':')[0]

            ts_response = session_bybit.set_trading_stop(
                category="linear",
                symbol=bybit_symbol,
                positionIdx=0,
                trailingStop=str(config.TRAILING_STOP_DISTANCE),
                activePrice=str(ts_trigger_price),
                #tpslMode="Partial"
            )

            if ts_response.get("retCode") == 0:
                remaining = 100 - int(tpsl_size)
                logger.info(
                    f"✅ Трейлинг-стоп на {remaining}% | Дист: {config.TRAILING_STOP_DISTANCE} | Актив: {ts_trigger_price:.2f}")
            else:
                logger.error(f"❌ Ошибка трейлинг-стопа: {ts_response.get('retMsg')}")

        except Exception as ts_error:
            logger.error(f"❌ Исключение трейлинг-стопа: {ts_error}")

        return True

    except Exception as e:
        logger.error(f"💥 Ошибка: {e}", exc_info=True)
        return False
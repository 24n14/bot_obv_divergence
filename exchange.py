import ccxt
import config
import logging
import requests

logger = logging.getLogger(__name__)



def exchange_start():
    try:
        # ============= ПРОКСИ =============
        proxy_url = (
            f"http://{config.PROXY_USER}:{config.PROXY_PASS}@"
            f"{config.PROXY_HOST}:{config.PROXY_PORT}"
        )

        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }

        # Проверка IP
        try:
            test_ip = requests.get('https://api.ipify.org', proxies=proxies, timeout=10).text
            logger.info(f"✅ Внешний IP через прокси: {test_ip}")
        except Exception as e:
            logger.error(f"❌ Не удалось проверить IP через прокси: {e}")

        # ============= БИРЖА =============
        exchange = ccxt.bybit({
            'apiKey': config.API_KEY,
            'secret': config.SECRET_KEY,
            'proxies': proxies if config.USE_PROXY else None,
            'enableRateLimit': True,
            'options': {
                'enableDemoTrading': config.DEMO_TRADING,
                'defaultType': 'linear',
                'adjustForTimeDifference': True,
                'recvWindow': 10000
            }
        })

        # Устанавливаем демо-режим, если нужен
        if config.DEMO_TRADING:
            exchange.urls['api'] = exchange.urls['demotrading']
            logger.info("🧪 ДЕМО-РЕЖИМ АКТИВИРОВАН")
        else:
            logger.info("⚠️ РЕАЛЬНАЯ ТОРГОВЛЯ!")

        # Тест авторизации и получение баланса
        balance = exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        logger.info(f"✅ АВТОРИЗАЦИЯ УСПЕШНА! Баланс: {usdt_balance} USDT")

        return exchange

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при подключении к бирже: {e}", exc_info=True)
        return None
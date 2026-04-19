import os
from dotenv import load_dotenv

load_dotenv()

#  ===== НАСТРОЙКИ ПОДКЛЮЧЕНИЯ =====
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
DEMO_TRADING = True  # True для демо-счета, False для реального
PROXY_HOST = '154.219.207.178'
PROXY_PORT = '63690'
PROXY_USER = os.getenv('PROXY_USER')
PROXY_PASS = os.getenv('PROXY_PASS')
USE_PROXY = True

#  ===== ПАРАМЕТРЫ ТОРГОВЛИ =====
SYMBOL = 'BTC/USDT:USDT'
CATEGORY = 'linear'
AMOUNT = 0.01
TIMEFRAME = '5m'
LIMIT = 100
LIMIT_CANDLES = 100
STOP_LOSS = 2
TAKE_PROFIT = 2
TRAILING_STOP_DISTANCE = 300

TPSL_SIZE = '50'
in_position = False
entry_price = 0.0
LEVERAGE = 10
MIN_AMOUNT = 0.001
#  ====ПАРАМЕТРЫ MOVING AVERAGE====
MA_PERIOD = 20
EMA_PERIOD = 10
# ===== MACD ПАРАМЕТРЫ =====
MACD_FAST = 12      # Быстрая линия (дефолт для MACD)
MACD_SLOW = 26      # Медленная линия
MACD_SIGNAL = 9     # Сигнальная линия

STOCH_K = 14
STOCH_D = 3
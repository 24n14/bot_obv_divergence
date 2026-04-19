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
STOP_LOSS = 1
TAKE_PROFIT = 2
TRAILING_STOP_DISTANCE = 150

TPSL_SIZE = '50'
in_position = False
entry_price = 0.0
LEVERAGE = 10
#MIN_AMOUNT = 0.001

# ===== ПАРАМЕТРЫ АНАЛИЗА ДИВЕРГЕНЦИИ =====
LOOKBACK = 50  # окно для анализа дивергенции
MIN_CONFIDENCE = 0.5  # минимальная уверенность для входа
MIN_CONFIDENCE_REVERSAL = 0.7  # уверенность для разворота позиции

# ===== ПАРАМЕТРЫ ИНДИКАТОРОВ =====
OBV_SMA_PERIOD = 5  # период сглажив��ния OBV
EMA_50_PERIOD = 50  # период EMA для тренда
ATR_PERIOD = 14  # период ATR для волатильности

# ===== КОЭФФИЦИЕНТЫ УВЕРЕННОСТИ =====
CONF_PRICE_STRENGTH = 0.2  # макс балл за силу цены
CONF_OBV_STRENGTH = 0.2  # макс балл за силу OBV
CONF_TIME_ALIGNMENT = 0.15  # макс балл за временное совпадение
CONF_VOLUME_CONFIRM = 0.15  # макс балл за объём
CONF_VOLATILITY = 0.15  # макс балл за волатильность
CONF_TREND_ALIGNMENT = 0.15  # макс балл за тренд

# ===== ПОРОГИ ВОЛАТИЛЬНОСТИ =====
VOLATILITY_OPTIMAL_LOW = 1.5
VOLATILITY_OPTIMAL_HIGH = 4.0
VOLATILITY_MAX = 8.0
VOLATILITY_MIN = 1.0

# ===== ПОРОГИ EMA =====
EMA_DEVIATION_PERCENT = 5  # 5% от EMA для сильного сигнала

# ===== ПРОЧИЕ ПАРАМЕТРЫ =====
MIN_CANDLES = 100  # минимум свечей для анализа
WAIT_RETRY_MAX = 3  # максимум попыток синхронизации
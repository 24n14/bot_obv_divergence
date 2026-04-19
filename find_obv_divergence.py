import numpy as np
import talib


def find_obv_divergence(high, low, close, volume, lookback=20):
    """
    Ищет дивергенцию между ценой и OBV с динамическим расчётом уверенности.
    """

    # 1. Рассчитываем OBV и его сглаженную версию
    obv = talib.OBV(close, volume)
    obv_sma = talib.SMA(obv, timeperiod=5)

    # 2. Берём срезы для анализа
    price = close[-lookback:]
    obv_slice = obv[-lookback:]
    obv_smooth = obv_sma[-lookback:]

    # 3. Находим локальные экстремумы
    price_min_idx, price_max_idx = find_local_extremes(price)
    obv_min_idx, obv_max_idx = find_local_extremes(obv_smooth)

    # 4. Ищем дивергенции
    result = None

    # БЫЧЬЯ дивергенция
    if len(price_min_idx) >= 2 and len(obv_min_idx) >= 2:
        last_min = price_min_idx[-1]
        prev_min = price_min_idx[-2]

        # Ищем соответствующие минимумы OBV
        last_obv_min = obv_min_idx[-1]
        # Находим предыдущий минимум OBV, который был до текущего
        prev_obv_min = obv_min_idx[-2] if len(obv_min_idx) >= 2 else last_obv_min

        price_down = price[last_min] < price[prev_min]
        obv_up = obv_smooth[last_obv_min] > obv_smooth[prev_obv_min]

        if price_down and obv_up:
            confidence, details = calculate_confidence_dynamic(
                price=price,
                obv=obv_smooth,
                price_idx=(prev_min, last_min),
                obv_idx=(prev_obv_min, last_obv_min),
                high=high[-lookback:], low=low[-lookback:],
                close=price, volume=volume[-lookback:],
                divergence_type='bullish'
            )
            result = ('bullish', confidence, details)

    # МЕДВЕЖЬЯ дивергенция
    if result is None and len(price_max_idx) >= 2 and len(obv_max_idx) >= 2:
        last_max = price_max_idx[-1]
        prev_max = price_max_idx[-2]

        last_obv_max = obv_max_idx[-1]
        prev_obv_max = obv_max_idx[-2] if len(obv_max_idx) >= 2 else last_obv_max

        price_up = price[last_max] > price[prev_max]
        obv_down = obv_smooth[last_obv_max] < obv_smooth[prev_obv_max]

        if price_up and obv_down:
            confidence, details = calculate_confidence_dynamic(
                price=price,
                obv=obv_smooth,
                price_idx=(prev_max, last_max),
                obv_idx=(prev_obv_max, last_obv_max),
                high=high[-lookback:], low=low[-lookback:],
                close=price, volume=volume[-lookback:],
                divergence_type='bearish'
            )
            result = ('bearish', confidence, details)

    if result:
        return result[0], result[1], result[2]
    return None, 0.0, {}

def find_local_extremes(arr):
    """Находит индексы локальных минимумов и максимумов"""
    min_idx = []
    max_idx = []
    for i in range(2, len(arr) - 2):
        if arr[i] < arr[i - 1] and arr[i] < arr[i - 2] and \
                arr[i] < arr[i + 1] and arr[i] < arr[i + 2]:
            min_idx.append(i)
        if arr[i] > arr[i - 1] and arr[i] > arr[i - 2] and \
                arr[i] > arr[i + 1] and arr[i] > arr[i + 2]:
            max_idx.append(i)
    return min_idx, max_idx


def calculate_confidence_dynamic(price, obv, price_idx, obv_idx,
                                 high, low, close, volume, divergence_type):
    """
    Рассчитывает уверенность в дивергенции на основе 6 рыночных факторов.
    Каждый фактор даёт от 0 до 0.2 баллов.
    """
    confidence = 0.0
    details = {}

    prev_price_idx, curr_price_idx = price_idx
    prev_obv_idx, curr_obv_idx = obv_idx

    # === ФАКТОР 1: Сила расхождения цены (0 - 0.2) ===
    if divergence_type == 'bullish':
        price_change = (price[curr_price_idx] - price[prev_price_idx]) / price[prev_price_idx]
        # Чем сильнее цена упала (отрицательное значение), тем лучше для бычьей дивергенции
        strength = min(abs(price_change) / 0.05, 1.0)  # 5% падения дают максимум
    else:  # bearish
        price_change = (price[curr_price_idx] - price[prev_price_idx]) / price[prev_price_idx]
        strength = min(price_change / 0.05, 1.0)  # 5% роста дают максимум

    factor1 = strength * 0.2
    confidence += factor1
    details['price_strength'] = round(factor1, 3)

    # === ФАКТОР 2: Сила расхождения OBV (0 - 0.2) ===
    if divergence_type == 'bullish':
        # OBV должен быть выше предыдущего минимума
        obv_change = (obv[curr_obv_idx] - obv[prev_obv_idx]) / abs(obv[prev_obv_idx] + 1e-6)
        strength = min(obv_change / 0.03, 1.0)  # 3% роста OBV дают максимум
    else:
        obv_change = (obv[prev_obv_idx] - obv[curr_obv_idx]) / abs(obv[prev_obv_idx] + 1e-6)
        strength = min(obv_change / 0.03, 1.0)

    factor2 = strength * 0.2
    confidence += factor2
    details['obv_strength'] = round(factor2, 3)

    # === ФАКТОР 3: Временное совпадение экстремумов (0 - 0.15) ===
    time_diff = abs(curr_price_idx - curr_obv_idx)
    if time_diff == 0:
        factor3 = 0.15
    elif time_diff <= 2:
        factor3 = 0.10
    elif time_diff <= 5:
        factor3 = 0.05
    else:
        factor3 = 0.0
    confidence += factor3
    details['time_alignment'] = factor3

    # === ФАКТОР 4: Объём на экстремуме (0 - 0.15) ===
    # Берём объём за 3 свечи вокруг экстремума
    volume_window = volume[max(0, curr_price_idx - 1):min(len(volume), curr_price_idx + 2)]
    avg_volume = np.mean(volume_window)
    historical_avg = np.mean(volume[max(0, curr_price_idx - 20):curr_price_idx])

    if historical_avg > 0:
        volume_ratio = avg_volume / historical_avg
        if divergence_type == 'bullish':
            # При бычьей дивергенции на минимуме должен быть высокий объём (паника)
            if volume_ratio > 1.5:
                factor4 = 0.15
            elif volume_ratio > 1.2:
                factor4 = 0.10
            else:
                factor4 = 0.05
        else:
            # При медвежьей дивергенции на максимуме высокий объём подтверждает разворот
            if volume_ratio > 1.5:
                factor4 = 0.15
            elif volume_ratio > 1.2:
                factor4 = 0.10
            else:
                factor4 = 0.05
    else:
        factor4 = 0.05
    confidence += factor4
    details['volume_confirm'] = factor4

    # === ФАКТОР 5: Волатильность рынка (0 - 0.15) ===
    # ATR (Average True Range) как % от цены
    atr = talib.ATR(high, low, close, timeperiod=14)[-1]
    current_price = close[-1]
    volatility_pct = (atr / current_price) * 100

    if 1.5 < volatility_pct < 4.0:  # Оптимальная волатильность
        factor5 = 0.15
    elif volatility_pct < 1.0 or volatility_pct > 8.0:  # Слишком тихо или слишком шумно
        factor5 = 0.03
    else:
        factor5 = 0.08
    confidence += factor5
    details['volatility'] = factor5

    # === ФАКТОР 6: Тренд более высокого таймфрейма (0 - 0.15) ===
    # Проверяем положение цены относительно EMA50
    ema50 = talib.EMA(close, timeperiod=50)[-1]
    current_price = close[-1]

    if divergence_type == 'bullish':
        # Бычья дивергенция сильнее, если цена ниже EMA50 (отскок от перепроданности)
        if current_price < ema50 * 0.95:  # на 5% ниже EMA
            factor6 = 0.15
        elif current_price < ema50:
            factor6 = 0.10
        else:
            factor6 = 0.05
    else:
        # Медвежья дивергенция сильнее, если цена выше EMA50
        if current_price > ema50 * 1.05:  # на 5% выше EMA
            factor6 = 0.15
        elif current_price > ema50:
            factor6 = 0.10
        else:
            factor6 = 0.05
    confidence += factor6
    details['trend_alignment'] = factor6

    # Итоговый confidence ограничиваем 1.0
    confidence = min(confidence, 1.0)
    details['total'] = round(confidence, 3)

    return confidence, details


# ============ ПРИМЕР ИСПОЛЬЗОВАНИЯ ============
'''
# Допустим, df — ваш DataFrame со свечами
close_prices = df['close'].values
high_prices = df['high'].values
low_prices = df['low'].values
volumes = df['volume'].values

signal, confidence, details = find_obv_divergence(
    high_prices, low_prices, close_prices, volumes, lookback=50
)

if signal:
    print(f"Сигнал: {signal}")
    print(f"Уверенность: {confidence:.2%}")
    print("Детали расчёта:")
    for key, value in details.items():
        print(f"  {key}: {value}")

    if confidence > 0.65:
        print("✅ ВХОДИМ в сделку")
    elif confidence > 0.5:
        print("⚠️ Входим с половинным объёмом")
    else:
        print("❌ Пропускаем — сигнал слабый")
'''
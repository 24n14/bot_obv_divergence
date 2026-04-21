import numpy as np
import talib
import logging

logger = logging.getLogger(__name__)


def find_obv_divergence(high, low, close, volume, lookback=20):
    """
    Ищет дивергенцию между ценой и OBV с улучшенной логикой детекции.
    """

    # Проверка на достаточность данных
    if len(close) < lookback + 50:  # +50 для EMA50
        logger.warning(f"Недостаточно данных: {len(close)} < {lookback + 50}")
        return None, 0.0, {}

    # 1. Рассчитываем OBV и его сглаженную версию
    obv = talib.OBV(close, volume)
    obv_sma = talib.SMA(obv, timeperiod=5)

    # 2. Работаем с полными массивами, но анализируем только последние lookback свечей
    start_idx = len(close) - lookback

    price_slice = close[start_idx:]
    obv_slice = obv[start_idx:]
    obv_smooth_slice = obv_sma[start_idx:]

    # 3. Находим локальные экстремумы
    price_min_idx, price_max_idx = find_local_extremes(price_slice)
    obv_min_idx, obv_max_idx = find_local_extremes(obv_smooth_slice)

    # Конвертируем в абсолютные индексы
    price_min_idx_abs = [start_idx + idx for idx in price_min_idx]
    price_max_idx_abs = [start_idx + idx for idx in price_max_idx]
    obv_min_idx_abs = [start_idx + idx for idx in obv_min_idx]
    obv_max_idx_abs = [start_idx + idx for idx in obv_max_idx]

    # 4. Ищем дивергенции
    best_signal = None
    best_confidence = 0.0
    best_details = {}

    # === БЫЧЬЯ дивергенция ===
    if len(price_min_idx_abs) >= 2 and len(obv_min_idx_abs) >= 2:
        for i in range(len(price_min_idx_abs) - 1):
            prev_min = price_min_idx_abs[i]
            curr_min = price_min_idx_abs[i + 1]

            # Улучшенный поиск соответствующих OBV минимумов
            obv_mins_nearby = find_nearby_extremes(
                obv_min_idx_abs,
                target_idx=curr_min,
                window=5  # ±5 свечей
            )

            if len(obv_mins_nearby) >= 2:
                prev_obv_min = obv_mins_nearby[0]
                curr_obv_min = obv_mins_nearby[-1]

                # Проверяем условие дивергенции
                price_down = close[curr_min] < close[prev_min]
                obv_up = obv_sma[curr_obv_min] > obv_sma[prev_obv_min]

                if price_down and obv_up:
                    confidence, details = calculate_confidence_dynamic(
                        price=close,  # Полный массив
                        obv=obv_sma,  # Полный массив
                        price_idx=(prev_min, curr_min),
                        obv_idx=(prev_obv_min, curr_obv_min),
                        high=high,
                        low=low,
                        close=close,
                        volume=volume,
                        divergence_type='bullish'
                    )

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_signal = 'bullish'
                        best_details = details
                        logger.debug(
                            f"🟢 BULLISH: price {close[prev_min]:.2f} → {close[curr_min]:.2f}, "
                            f"OBV {obv_sma[prev_obv_min]:.0f} → {obv_sma[curr_obv_min]:.0f}, "
                            f"conf: {confidence:.2%}"
                        )

    # === МЕДВЕЖЬЯ дивергенция ===
    if len(price_max_idx_abs) >= 2 and len(obv_max_idx_abs) >= 2:
        for i in range(len(price_max_idx_abs) - 1):
            prev_max = price_max_idx_abs[i]
            curr_max = price_max_idx_abs[i + 1]

            obv_maxs_nearby = find_nearby_extremes(
                obv_max_idx_abs,
                target_idx=curr_max,
                window=5
            )

            if len(obv_maxs_nearby) >= 2:
                prev_obv_max = obv_maxs_nearby[0]
                curr_obv_max = obv_maxs_nearby[-1]

                price_up = close[curr_max] > close[prev_max]
                obv_down = obv_sma[curr_obv_max] < obv_sma[prev_obv_max]

                if price_up and obv_down:
                    confidence, details = calculate_confidence_dynamic(
                        price=close,
                        obv=obv_sma,
                        price_idx=(prev_max, curr_max),
                        obv_idx=(prev_obv_max, curr_obv_max),
                        high=high,
                        low=low,
                        close=close,
                        volume=volume,
                        divergence_type='bearish'
                    )

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_signal = 'bearish'
                        best_details = details
                        logger.debug(
                            f"🔴 BEARISH: price {close[prev_max]:.2f} → {close[curr_max]:.2f}, "
                            f"OBV {obv_sma[prev_obv_max]:.0f} → {obv_sma[curr_obv_max]:.0f}, "
                            f"conf: {confidence:.2%}"
                        )

    if best_signal:
        return best_signal, best_confidence, best_details
    return None, 0.0, {}


def find_nearby_extremes(extremes_list, target_idx, window=5):
    """
    Находит экстремумы в пределах window от target_idx
    """
    nearby = []
    for idx in extremes_list:
        if abs(idx - target_idx) <= window:
            nearby.append(idx)
    return sorted(nearby)


def find_local_extremes(arr, min_distance=2):
    """
    Находит индексы локальных минимумов и максимумов
    """
    min_idx = []
    max_idx = []

    for i in range(min_distance, len(arr) - min_distance):
        # Проверка на минимум
        is_min = True
        is_max = True

        for j in range(1, min_distance + 1):
            if arr[i] >= arr[i - j] or arr[i] >= arr[i + j]:
                is_min = False
            if arr[i] <= arr[i - j] or arr[i] <= arr[i + j]:
                is_max = False

        if is_min:
            # Проверяем, не слишком ли близко к предыдущему минимуму
            if not min_idx or i - min_idx[-1] >= min_distance:
                min_idx.append(i)

        if is_max:
            if not max_idx or i - max_idx[-1] >= min_distance:
                max_idx.append(i)

    return min_idx, max_idx


def calculate_confidence_dynamic(price, obv, price_idx, obv_idx,
                                 high, low, close, volume, divergence_type):
    """
    Рассчитывает уверенность в дивергенции
    """
    confidence = 0.0
    details = {}

    prev_price_idx, curr_price_idx = price_idx
    prev_obv_idx, curr_obv_idx = obv_idx

    # === ФАКТОР 1: Сила расхождения цены (0 - 0.25) ===
    if divergence_type == 'bullish':
        price_change = (price[curr_price_idx] - price[prev_price_idx]) / abs(price[prev_price_idx] + 1e-8)
        strength = min(abs(price_change) / 0.03, 1.0)
    else:
        price_change = (price[curr_price_idx] - price[prev_price_idx]) / abs(price[prev_price_idx] + 1e-8)
        strength = min(price_change / 0.03, 1.0)

    factor1 = strength * 0.25
    confidence += factor1
    details['price_strength'] = round(factor1, 3)

    # === ФАКТОР 2: Сила расхождения OBV (0 - 0.25) ===
    if divergence_type == 'bullish':
        obv_change = (obv[curr_obv_idx] - obv[prev_obv_idx]) / (abs(obv[prev_obv_idx]) + 1e-8)
        strength = min(max(obv_change, 0) / 0.02, 1.0)
    else:
        obv_change = (obv[prev_obv_idx] - obv[curr_obv_idx]) / (abs(obv[prev_obv_idx]) + 1e-8)
        strength = min(max(obv_change, 0) / 0.02, 1.0)

    factor2 = strength * 0.25
    confidence += factor2
    details['obv_strength'] = round(factor2, 3)

    # === ФАКТОР 3: Временное совпадение (0 - 0.15) ===
    time_diff = abs(curr_price_idx - curr_obv_idx)
    if time_diff <= 1:
        factor3 = 0.15
    elif time_diff <= 3:
        factor3 = 0.12
    elif time_diff <= 5:
        factor3 = 0.08
    else:
        factor3 = 0.03
    confidence += factor3
    details['time_alignment'] = factor3

    # === ФАКТОР 4: Объём на экстремуме (0 - 0.15) ===
    # Безопасный расчет с проверкой границ
    vol_start = max(0, curr_price_idx - 2)
    vol_end = min(len(volume), curr_price_idx + 3)
    volume_window = volume[vol_start:vol_end]

    hist_start = max(0, curr_price_idx - 30)
    hist_end = max(1, curr_price_idx)
    historical_volume = volume[hist_start:hist_end]

    if len(volume_window) > 0 and len(historical_volume) > 0:
        avg_volume = np.mean(volume_window)
        historical_avg = np.mean(historical_volume)

        if historical_avg > 0:
            volume_ratio = avg_volume / historical_avg
            if volume_ratio > 1.5:
                factor4 = 0.15
            elif volume_ratio > 1.2:
                factor4 = 0.12
            elif volume_ratio > 0.8:
                factor4 = 0.08
            else:
                factor4 = 0.04
        else:
            factor4 = 0.05
    else:
        factor4 = 0.05

    confidence += factor4
    details['volume_confirm'] = factor4

    # === ФАКТОР 5: Волатильность (0 - 0.1) ===
    try:
        atr = talib.ATR(high, low, close, timeperiod=14)
        if len(atr) > 0 and not np.isnan(atr[-1]):
            current_atr = atr[-1]
            current_price = close[-1]
            if current_price > 0:
                volatility_pct = (current_atr / current_price) * 100
            else:
                volatility_pct = 2.0
        else:
            volatility_pct = 2.0
    except:
        volatility_pct = 2.0

    if 1.0 < volatility_pct < 5.0:
        factor5 = 0.1
    elif 0.5 < volatility_pct <= 1.0 or 5.0 <= volatility_pct < 8.0:
        factor5 = 0.06
    else:
        factor5 = 0.03

    confidence += factor5
    details['volatility'] = factor5

    # === ФАКТОР 6: Тренд (0 - 0.1) ===
    try:
        if len(close) >= 50:
            ema50 = talib.EMA(close, timeperiod=50)[-1]
        else:
            ema50 = np.mean(close[-20:]) if len(close) >= 20 else close[-1]
    except:
        ema50 = close[-1]

    current_price = close[-1]

    if divergence_type == 'bullish':
        if current_price < ema50 * 0.95:
            factor6 = 0.10
        elif current_price < ema50:
            factor6 = 0.07
        else:
            factor6 = 0.03
    else:
        if current_price > ema50 * 1.05:
            factor6 = 0.10
        elif current_price > ema50:
            factor6 = 0.07
        else:
            factor6 = 0.03

    confidence += factor6
    details['trend_alignment'] = factor6

    confidence = min(confidence, 1.0)
    details['total'] = round(confidence, 3)

    return confidence, details
import numpy as np
import pandas as pd

##### TODO #########################################
### IMPLEMENT 'getMyPosition' FUNCTION #############
### TO RUN, RUN 'eval.py' ##########################

nInst = 50
currentPos = np.zeros(nInst)
ma_signal_history = None
core_stock_id = {1,5,8,12,15,16,18,29,30,34,46}
# Signal Count
signal_count = np.zeros(nInst, dtype=int)      # 连续同方向信号数
last_signal_dir = np.zeros(nInst, dtype=int)   # 上次信号方向


cash_limit = 2000
commRate = 0.0005
dollar_position_limit = 10000

######################################################
## Backtesting Parameters
######################################################

trading_logs = {
    'cash_history':  pd.DataFrame(columns=range(nInst)),
    'position_history': pd.DataFrame(columns=range(nInst)),
    'volume_history': pd.DataFrame(columns=range(nInst))
}

######################################################
## MA History and Signals
######################################################

signals = {
    'ma_signals': {
        '5_15': pd.DataFrame(columns=range(nInst)),
        '5_20': pd.DataFrame(columns=range(nInst)),
        '5_30': pd.DataFrame(columns=range(nInst)),
        '10_30': pd.DataFrame(columns=range(nInst)),
        '10_60': pd.DataFrame(columns=range(nInst)),
        '10_90': pd.DataFrame(columns=range(nInst)),
        '15_60': pd.DataFrame(columns=range(nInst)),
        '15_30': pd.DataFrame(columns=range(nInst)),
        '15_90': pd.DataFrame(columns=range(nInst)),
        '20_60': pd.DataFrame(columns=range(nInst)),
        '20_90': pd.DataFrame(columns=range(nInst)),
        '20_100': pd.DataFrame(columns=range(nInst)),
        '30_180': pd.DataFrame(columns=range(nInst)),
        '60_180': pd.DataFrame(columns=range(nInst)),
        '60_360': pd.DataFrame(columns=range(nInst)),
        '120_360': pd.DataFrame(columns=range(nInst)),
        '180_360': pd.DataFrame(columns=range(nInst))
    },
    # 'rsi_signals': {
    #     '14': pd.DataFrame(columns=range(nInst))
    # }
}
ma_history = {
    '5': pd.DataFrame(columns=range(nInst)),
    '10': pd.DataFrame(columns=range(nInst)),
    '15': pd.DataFrame(columns=range(nInst)),
    '20': pd.DataFrame(columns=range(nInst)),
    '30': pd.DataFrame(columns=range(nInst)),
    '60': pd.DataFrame(columns=range(nInst)),
    '90': pd.DataFrame(columns=range(nInst)),
    '100': pd.DataFrame(columns=range(nInst)),
    '120': pd.DataFrame(columns=range(nInst)),
    '180': pd.DataFrame(columns=range(nInst)),
    '360': pd.DataFrame(columns=range(nInst))
}
rsi_history = {

}




# Bollinger Bands
bollinger_band = {
    'mid': pd.DataFrame(columns=range(nInst)),
    'upper': pd.DataFrame(columns=range(nInst)),
    'lower': pd.DataFrame(columns=range(nInst))
}

######################################################
## Strategies
######################################################


def getMyPosition(prcSoFar: np.ndarray) -> np.ndarray:
    global currentPos, signals, ma_history, trading_logs, cash_limit, dynamic_stock_pool, core_stock_id
    
    update_ma_history(prcSoFar)
    update_bollinger_bands(prcSoFar)
    update_ma_signal(prcSoFar)
    
    pos_ma = ma_strategy(prcSoFar, dollar_limit=cash_limit)
    # pos_brs = bollinger_reversal_strategy(prcSoFar)
    
    currentPos = pos_ma
    update_trading_logs(prcSoFar)
    return currentPos


#############################################################
# MA Strategy

def ma_strategy(prcSoFar: np.ndarray, dollar_limit: float = 6000) -> np.ndarray:
    global currentPos, signals, signal_count, last_signal_dir

    last_prices = prcSoFar[:, -1]

    # 汇总所有 ma_signals
    regime = detect_market_regime(prcSoFar)
    selected_keys = get_filtered_ma_signals(regime)

    final_signal = np.zeros(nInst)
    for key in selected_keys:
        final_signal += signals['ma_signals'][key].iloc[-1].values

    current_position = currentPos.copy()
    target_position = current_position.copy()

    for i in range(nInst):
        signal = int(np.sign(final_signal[i]))  # 当前信号方向
        last_dir = last_signal_dir[i]
        price = last_prices[i]

        # 方向反转：清仓并重置信号计数
        if signal != 0 and signal != last_dir and current_position[i] != 0:
            target_position[i] = 0
            signal_count[i] = 0

        # 同方向累积信号：增加 count
        if signal != 0:
            if signal != last_signal_dir[i]:
                signal_count[i] = 1  # 新方向开始
            else:
                signal_count[i] += 1  # 新方向开始累积

            # Apply Sigmoid Function to calculate signal strength
            base_unit = cash_limit / price
            a = 1.2
            b = 4
            max_mult = 5

            multiplier = ((1 - np.exp(-a * signal_count[i])) ** b) * max_mult
            # multiplier = signal_count[i]

            pos = round(signal * base_unit * multiplier)

            # pos = round(signal * base_unit * signal_count[i])
            target_position[i] = pos

            last_signal_dir[i] = signal

    # 布林止盈止损
    if len(bollinger_band['upper']) > 0:
        price = last_prices
        upper = bollinger_band['upper'].iloc[-1].values
        lower = bollinger_band['lower'].iloc[-1].values

        target_position[(current_position > 0) & (price < lower)] = 0
        target_position[(current_position < 0) & (price > upper)] = 0
        target_position[(current_position > 0) & (price >= upper * 1.02)] = 0
        target_position[(current_position < 0) & (price <= lower * 0.98)] = 0

    # 股票池限制
    for i in range(nInst):
        if i not in core_stock_id:
            target_position[i] = 0

    return target_position

#############################################################
# Bollinger Reversal Strategy
#############################################################

def bollinger_reversal_strategy(prcSoFar: np.ndarray, dollar_limit: float = 1000) -> np.ndarray:
    global bollinger_band, currentPos, dynamic_stock_pool

    last_prices = prcSoFar[:, -1]
    current_position = currentPos.copy()
    target_position = np.zeros_like(current_position)

    if len(bollinger_band['upper']) == 0:
        return target_position  # 没有布林带数据，不操作


    upper = bollinger_band['upper'].iloc[-1].values
    lower = bollinger_band['lower'].iloc[-1].values
    mid = bollinger_band['mid'].iloc[-1].values

    active_flags = is_active(prcSoFar)

    for i in range(nInst):
        if not active_flags[i]:
            continue  # 跳过不活跃的股票

        price = last_prices[i]

        if price < lower[i]:
            target_position[i] = 0
        elif current_position[i] == 0 and price >= lower[i] and price < mid[i]:
            shares = int(dollar_limit / price)
            target_position[i] = shares

        elif price > upper[i]:
            target_position[i] = 0
        elif current_position[i] == 0 and price <= upper[i] and price > mid[i]:
            shares = int(dollar_limit / price)
            target_position[i] = -shares

        if current_position[i] > 0 and price >= mid[i]:
            target_position[i] = 0
        if current_position[i] < 0 and price <= mid[i]:
            target_position[i] = 0

    return target_position



#####################################################################################
# Update trading logs
#####################################################################################

def update_trading_logs(prcSoFar: np.ndarray):
    """
    Update the trading logs based on the current position and prices.
    """
    global trading_logs, currentPos

    # Update the position history
    update_position_history(prcSoFar)
    # Update cash history
    update_cash_history(prcSoFar)

def update_position_history(prcSoFar: np.ndarray):
    """
    Update the position history based on the current position.
    """
    global trading_logs, currentPos

    # Update the position history
    trading_logs['position_history'].loc[len(trading_logs['position_history'])] = currentPos

def update_cash_history(prcSoFar: np.ndarray):
    """
    Update the NAV history based on the current position and prices.
    """
    global trading_logs, currentPos
    if len(trading_logs['position_history']) < 2:
    # Initialization
        trading_logs['cash_history'].loc[len(trading_logs['cash_history'])] = np.zeros(nInst)
        return
    # Calculate the cash based on the current position

    price_t1 = prcSoFar[:, -1]
    position_t2 = trading_logs['position_history'].iloc[-2]
    position_t1 = trading_logs['position_history'].iloc[-1]

    delta_position = position_t1 - position_t2
    delta_volume = np.abs(price_t1 * delta_position)

    trading_logs['volume_history'].loc[len(trading_logs['volume_history'])] = delta_volume

    commission_fee = delta_volume * commRate
    cash_t2 = trading_logs['cash_history'].iloc[-1]

    trading_logs['cash_history'].loc[len(trading_logs['cash_history'])] = cash_t2 - delta_position * price_t1 - commission_fee


######################################################################################
# Moving Average History and Signals
######################################################################################

def update_ma_history(prcSoFar: np.array):
    """
    Update the moving average history for different windows.
    """
    global ma_history

    prc_so_far = prcSoFar.copy()
    (n_inst, n_days) = prc_so_far.shape
    
    for window in ma_history.keys():
        window_size = int(window)
        if n_days >= window_size + 1:
            ma = np.mean(prc_so_far[:, -window_size:], axis=1)
            ma_history[window].loc[len(ma_history[window])] = ma
        else:
            ma_history[window].loc[len(ma_history[window])] = np.full(n_inst, np.nan)

def update_ma_signal(prcSoFar:np.array):
    global signals, ma_history

    ma_signals = signals['ma_signals']
    prc_so_far = prcSoFar.copy()
    (n_inst, n_days) = prc_so_far.shape

    for key in ma_signals.keys():
        short_window, long_window = map(int, key.split('_'))
        if n_days < long_window + 1:
            ma_signals[key].loc[len(ma_signals[key])] = np.zeros(n_inst)
            continue
    
        ma_short = np.mean(prc_so_far[:, -short_window:], axis=1)
        ma_long = np.mean(prc_so_far[:, -long_window:], axis=1)

        curr = np.sign(ma_short - ma_long)

        if len(ma_history[str(short_window)]) < 2 or len(ma_history[str(long_window)]) < 2:
            ma_signals[key].loc[len(ma_signals[key])] = np.zeros(n_inst)
            continue

        # Because we already updated ma_history in the function called before this, we use -2 as index
        prev = np.sign(ma_history[str(short_window)].iloc[-2].values - ma_history[str(long_window)].iloc[-2].values)

        gold_cross  = (prev == -1) & (curr == 1)
        death_cross = (prev == 1) & (curr == -1)

        signal = np.zeros(n_inst)
        signal[gold_cross] = 1
        signal[death_cross] = -1

        ma_signals[key].loc[len(ma_signals[key])] = signal

########################################################################################
# Bollinger Bands
########################################################################################

def update_bollinger_bands(prcSoFar: np.ndarray, window: int = 20, num_std: float = 2.0):
    """
    Update the Bollinger Bands for the given prices.
    """
    global bollinger_band

    prc_so_far = prcSoFar.copy()
    (n_inst, n_days) = prc_so_far.shape

    if n_days < window + 1:
        return

    mid_band = np.mean(prc_so_far[:, -window:], axis=1)
    std_dev = np.std(prc_so_far[:, -window:], axis=1)

    bollinger_band['mid'].loc[len(bollinger_band['mid'])] = mid_band
    bollinger_band['upper'].loc[len(bollinger_band['upper'])] = mid_band + num_std * std_dev
    bollinger_band['lower'].loc[len(bollinger_band['lower'])] = mid_band - num_std * std_dev

#######################################################################################
# Return functions for history and signals
#######################################################################################

def get_ma_history():
    """
    Get the moving average history for different windows.
    """
    return ma_history.copy()

def get_signals():
    """
    Get the all signals
    """
    return signals

def get_ma_signals():
    """
    Get the moving average signals for different windows.
    """
    return signals['ma_signals'].copy()

def get_trading_logs():
    """
    Get the trading logs including NAV and position history.
    """
    return trading_logs.copy()

########################################################################################
# Reset functions
########################################################################################

def reset_logs():
    global currentPos, trading_logs, ma_history, signals, ma_signal_history

    currentPos = np.zeros(nInst)

    for key in trading_logs:
        trading_logs[key] = pd.DataFrame(columns=range(nInst))

    for key in ma_history:
        ma_history[key] = pd.DataFrame(columns=range(nInst))

    for key in signals:
        for k in signals[key]:
            signals[key][k] = pd.DataFrame(columns=range(nInst))

    ma_signal_history = None

#######################################################################################
# Detect Market Regime

def detect_market_regime(prcSoFar: np.ndarray, window: int = 20, lookback: int = 15) -> int:
    global bollinger_band

    if len(bollinger_band['upper']) < lookback:
        return 0  # 数据不够，保持中性

    upper = np.stack(bollinger_band['upper'].iloc[-lookback:].values)
    lower = np.stack(bollinger_band['lower'].iloc[-lookback:].values)
    width_hist = np.mean(upper - lower, axis=1)

    latest_width = np.mean(bollinger_band['upper'].iloc[-1].values - bollinger_band['lower'].iloc[-1].values)

    q_high = np.quantile(width_hist, 0.80)
    q_low = np.quantile(width_hist, 0.20)

    if latest_width > q_high:
        return 1  # trend
    elif latest_width < q_low:
        return -1  # sideways
    else:
        return 0  # neutral

    
def get_filtered_ma_signals(regime: int) -> list:
    all_keys = list(signals['ma_signals'].keys())
    if regime <= 0:
        # 非趋势期：去除短线
        return [key for key in all_keys if not key.startswith('5_')]
    else:
        return all_keys
import numpy as np
import pandas as pd

##### TODO #########################################
### IMPLEMENT 'getMyPosition' FUNCTION #############
### TO RUN, RUN 'eval.py' ##########################

nInst = 50
currentPos = np.zeros(nInst)
ma_signal_history = None
ma_stock_id = [1,5,8,12,15,16,18,29,30,34,46]
# Signal Count
signal_count = np.zeros(nInst, dtype=int)      # 连续同方向信号数
last_signal_dir = np.zeros(nInst, dtype=int)   # 上次信号方向


cash_limit = 1000
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
        #'2_5': pd.DataFrame(columns=range(nInst)),
        #'2_10': pd.DataFrame(columns=range(nInst)),
        #'2_15': pd.DataFrame(columns=range(nInst)),
        '5_15': pd.DataFrame(columns=range(nInst)),
        '5_20': pd.DataFrame(columns=range(nInst)),
        '5_30': pd.DataFrame(columns=range(nInst)),
        #'5_60': pd.DataFrame(columns=range(nInst)),
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
    '2': pd.DataFrame(columns=range(nInst)),
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




# Blinger Bands
bollinger_band = {
    'mid': pd.DataFrame(columns=range(nInst)),
    'upper': pd.DataFrame(columns=range(nInst)),
    'lower': pd.DataFrame(columns=range(nInst))
}
#####################################################


def getMyPosition(prcSoFar: np.ndarray) -> np.ndarray:
    # update the position based on the latest prices
    global currentPos, signals, ma_history, trading_logs, cash_limit
    update_ma_history(prcSoFar)
    update_bollinger_bands(prcSoFar)
    update_ma_signal(prcSoFar)

    currentPos = ma_strategy(prcSoFar, dollar_limit=cash_limit)

    update_trading_logs(prcSoFar)

    return currentPos


def ma_strategy(prcSoFar: np.ndarray, dollar_limit: float = 5000) -> np.ndarray:
    global currentPos, signals, signal_count, last_signal_dir

    (n_inst, n_days) = prcSoFar.shape
    last_prices = prcSoFar[:, -1]

    # 汇总所有 ma_signals
    final_signal = np.sum(
        np.stack([df.iloc[-1].values for df in signals['ma_signals'].values()]),
        axis=0
    )

    current_position = currentPos.copy()
    target_position = current_position.copy()

    for i in range(n_inst):
        signal = int(np.sign(final_signal[i]))  # 当前信号方向
        last_dir = last_signal_dir[i]
        price = last_prices[i]

        # 方向反转：清仓并重置信号计数
        if signal != 0 and signal != last_dir and current_position[i] != 0:
            target_position[i] = 0
            signal_count[i] = 0

        # 同方向累积信号：增加 count
        if signal != 0:
            signal_count[i] += 1  # 新方向开始累积

            base_unit = cash_limit / price
            k = 1.4       # 增速
            x0 = 3     # 中心位置，越小越早拉满
            max_mult = 8  # 最大放大倍数

            multiplier = (np.tanh(k * ( - x0)) + 1) / 2 * max_mult

            pos = round(signal * base_unit * signal_count[i])
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
    for i in range(n_inst):
        if i not in ma_stock_id:
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

        # # Blinger Bands Filter
        # if len(bollinger_band['upper']) > 0:
        #     price = prcSoFar[:, -1]
        #     upper_band = bollinger_band['upper'].iloc[-1].values
        #     lower_band = bollinger_band['lower'].iloc[-1].values

        #     # 多信号 + 价格过高（>= 上轨）→ 无效
        #     signal[(signal > 0) & (price >= upper_band)] = 0
        #     # 空信号 + 价格过低（<= 下轨）→ 无效
        #     signal[(signal < 0) & (price <= lower_band)] = 0

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
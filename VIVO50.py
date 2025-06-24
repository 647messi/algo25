import numpy as np
import pandas as pd

##### TODO #########################################
### IMPLEMENT 'getMyPosition' FUNCTION #############
### TO RUN, RUN 'eval.py' ##########################

nInst = 50
currentPos = np.zeros(nInst)
ma_signal_history = None
signals = {}
ma_history = {
    '5': pd.DataFrame(columns=range(nInst)),
    '20': pd.DataFrame(columns=range(nInst)),
    '30': pd.DataFrame(columns=range(nInst)),
    '60': pd.DataFrame(columns=range(nInst)),
    '180': pd.DataFrame(columns=range(nInst))
}

signals['30_180'] = pd.DataFrame(columns=range(nInst))



def getMyPosition(prcSoFar: np.ndarray) -> np.ndarray:
    # update the position based on the latest prices
    # currentPos = ma_strategy(prcSoFar, short_window=30, long_window=180, dollar_limit=10000, delay=0)
    update_ma_history(prcSoFar)
    update_ma_signal(prcSoFar)

    currentPos = ma_strategy_using_signals(prcSoFar, signal_key='30_180', dollar_limit=10000)

    return currentPos

def ma_strategy_using_signals(prcSoFar: np.ndarray, signal_key: str = '30_180', dollar_limit: float = 10000) -> np.ndarray:
    if len(signals[signal_key]) == 0:
        return np.zeros(prcSoFar.shape[0])

    latest_signal = signals[signal_key].iloc[-1].values
    cur_price = prcSoFar[:, -1]
    position = (latest_signal * dollar_limit / cur_price).astype(int)

    return position


# def ma_strategy(prcSoFar: np.ndarray, short_window: int = 5, long_window: int = 20, dollar_limit: float = 8000, delay: int = 0) -> np.ndarray:

#     (n_inst, n_days) = prcSoFar.shape
    

#     if n_days < long_window+1:
#         return np.zeros(n_inst)
    

#     cur_price = prcSoFar[:, -1]
    
#     # Calculate the moving average
#     ma_short = np.mean(prcSoFar[:, -short_window:], axis=1)
#     ma_long  = np.mean(prcSoFar[:, -long_window:], axis=1)

#     curr = np.sign(ma_short - ma_long)

#     # Initialize history signal array
#     global ma_signal_history

#     if ma_signal_history is None:
#         ma_signal_history = np.zeros((n_inst, delay+2))

#     # Shift the history to the left
#     ma_signal_history[:, :-1] = ma_signal_history[:, 1:]
#     ma_signal_history[:, -1] = curr  # t 时刻趋势方向

#     # 判断 t-3 是否是金叉 or 死叉
#     is_gold_cross  = (ma_signal_history[:, 0] == -1) & (ma_signal_history[:, 1] ==  1)
#     is_death_cross = (ma_signal_history[:, 0] ==  1) & (ma_signal_history[:, 1] == -1)

#     # 检查 t-2, t-1, t 是否持续维持趋势
#     gold_trend_held  = np.all(ma_signal_history[:, 2:] == 1, axis=1)
#     death_trend_held = np.all(ma_signal_history[:, 2:] == -1, axis=1)

#     # 触发建仓
#     buy_signal  = is_gold_cross  & gold_trend_held
#     sell_signal = is_death_cross & death_trend_held

#     # 可选过滤震荡区间
#     # neutral_zone = np.abs(signal_sum) <= 1

#     final_signal = np.zeros(n_inst)
#     final_signal[buy_signal] = 1
#     final_signal[sell_signal] = -1

#     position = (final_signal * dollar_limit / cur_price).astype(int)
    
#     return position

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

    prc_so_far = prcSoFar.copy()
    (n_inst, n_days) = prc_so_far.shape

    for key in signals.keys():
        short_window, long_window = map(int, key.split('_'))
        if n_days < long_window + 1:
            signals[key].loc[len(signals[key])] = np.zeros(n_inst)
            continue
    
        ma_short = np.mean(prc_so_far[:, -short_window:], axis=1)
        ma_long = np.mean(prc_so_far[:, -long_window:], axis=1)

        curr = np.sign(ma_short - ma_long)
        # Because we already updated ma_history in the function called before this, we use -2 as index
        prev = np.sign(ma_history[str(short_window)].iloc[-2].values - ma_history[str(long_window)].iloc[-2].values)

        gold_cross  = (prev == -1) & (curr == 1)
        death_cross = (prev == 1) & (curr == -1)

        signal = np.zeros(n_inst)
        signal[gold_cross] = 1
        signal[death_cross] = -1

        signals[key].loc[len(signals[key])] = signal


def get_ma_history():
    """
    Get the moving average history for different windows.
    """
    return ma_history

def get_ma_signal():
    """
    Get the moving average signals for different windows.
    """
    return signals
import numpy as np

##### TODO #########################################
### IMPLEMENT 'getMyPosition' FUNCTION #############
### TO RUN, RUN 'eval.py' ##########################

nInst = 50
# use a global variable to store moving average signals for the delay in the strategy
ma_signal_history = None


def getMyPosition(prcSoFar: np.ndarray) -> np.ndarray:
    # update the position based on the latest prices
    currentPos = ma2_strategy(prcSoFar, short_window=30, long_window=180, dollar_limit=3000, delay=0)
    
    return currentPos

def ma2_strategy(prcSoFar: np.ndarray, short_window: int = 5, long_window: int = 20, dollar_limit: float = 8000, delay: int = 0) -> np.ndarray:

    (n_inst, n_days) = prcSoFar.shape
    
    if n_days < long_window+1:
        return np.zeros(n_inst)

    cur_price = prcSoFar[:, -1]
    
    # Calculate the moving average
    ma_short = np.mean(prcSoFar[:, -short_window:], axis=1)
    ma_long  = np.mean(prcSoFar[:, -long_window:], axis=1)

    curr = np.sign(ma_short - ma_long)

    # Initialize history signal array
    global ma_signal_history

    if ma_signal_history is None:
        ma_signal_history = np.zeros((n_inst, delay+2))

    # Shift the history to the left
    ma_signal_history[:, :-1] = ma_signal_history[:, 1:]
    ma_signal_history[:, -1] = curr  # t 时刻趋势方向

    # 判断 t-3 是否是金叉 or 死叉
    is_gold_cross  = (ma_signal_history[:, 0] == -1) & (ma_signal_history[:, 1] ==  1)
    is_death_cross = (ma_signal_history[:, 0] ==  1) & (ma_signal_history[:, 1] == -1)

    # 检查 t-2, t-1, t 是否持续维持趋势
    gold_trend_held  = np.all(ma_signal_history[:, 2:] == 1, axis=1)
    death_trend_held = np.all(ma_signal_history[:, 2:] == -1, axis=1)

    # 触发建仓
    buy_signal  = is_gold_cross  & gold_trend_held
    sell_signal = is_death_cross & death_trend_held

    # 可选过滤震荡区间
    # neutral_zone = np.abs(signal_sum) <= 1

    final_signal = np.zeros(n_inst)
    final_signal[buy_signal] = 1
    final_signal[sell_signal] = -1

    position = (final_signal * dollar_limit / cur_price).astype(int)
    
    return position


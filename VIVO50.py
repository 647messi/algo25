import numpy as np
import pandas as pd

##### TODO #########################################
### IMPLEMENT 'getMyPosition' FUNCTION #############
### TO RUN, RUN 'eval.py' ##########################

nInst = 50
currentPos = np.zeros(nInst)
ma_signal_history = None

cash_limit = 9000
commRate = 0.0005

######################################################
## Backtesting Parameters
######################################################

nav_history = None  # NAV history
position_history = None  # Position history

######################################################
## MA History and Signals
######################################################

signals = {}
ma_history = {
    '5': pd.DataFrame(columns=range(nInst)),
    '20': pd.DataFrame(columns=range(nInst)),
    '30': pd.DataFrame(columns=range(nInst)),
    '60': pd.DataFrame(columns=range(nInst)),
    '180': pd.DataFrame(columns=range(nInst))
}


signals['30_180'] = pd.DataFrame(columns=range(nInst))
signals['5_20'] = pd.DataFrame(columns=range(nInst))
signals['30_60'] = pd.DataFrame(columns=range(nInst))
#####################################################


def getMyPosition(prcSoFar: np.ndarray) -> np.ndarray:
    # update the position based on the latest prices
    global currentPos, signals, ma_history, nav_history, position_history

    update_trading_logs(prcSoFar)

    update_ma_history(prcSoFar)
    update_ma_signal(prcSoFar)

    # currentPos = ma_strategy_using_signals(prcSoFar, signal_key='30_180', dollar_limit=10000)

    currentPos = ma_strategy(prcSoFar, dollar_limit=cash_limit)

    return currentPos

# def ma_strategy_using_signals(prcSoFar: np.ndarray, signal_key: str = '30_180', dollar_limit: float = 10000) -> np.ndarray:
#     if len(signals[signal_key]) == 0:
#         return np.zeros(prcSoFar.shape[0])

#     latest_signal = signals[signal_key].iloc[-1].values
#     cur_price = prcSoFar[:, -1]
#     position = (latest_signal * dollar_limit / cur_price).astype(int)

#     return position

def ma_strategy(prcSoFar: np.ndarray, dollar_limit: float = 10000) -> np.ndarray:
    global currentPos, signals, ma_history

    (n_inst, n_days) = prcSoFar.shape
    last_prices = prcSoFar[:, -1]
    

    # Get signals

    # all_signals = []
    # for signal_key in signals:
    #     if len(signals[signal_key]) > 0:
    #         all_signals.append(signals[signal_key].iloc[-1].values)
    # all_signals = np.array(all_signals)

    # final_signal = np.zeros(n_inst)
    # for signal_key in signals.keys():
    #     final_signal += signals[signal_key].iloc[-1].values

    all_signals = np.array([
        signals[key].iloc[-1].values for key in signals if len(signals[key]) > 0
    ])

    max_signal = np.max(all_signals, axis=0)
    min_signal = np.min(all_signals, axis=0)

    # Update current position based on the signal
    # Use last day prices to estimate the postion
    # currentPos += final_signal * (dollar_limit / last_prices).astype(int)

    new_position = currentPos.copy()

    unit = (dollar_limit / last_prices).astype(int)

    # 做空：如果 min_signal == -1
    short_mask = (min_signal == -1)
    long_mask = (max_signal == 1)

    # 如果当前是多仓 → 清仓并做空
    reverse_mask = short_mask & (currentPos > 0)
    new_position[reverse_mask] = -unit[reverse_mask]

    # 如果已经是空仓 → 继续加空
    add_short_mask = short_mask & (currentPos <= 0)
    new_position[add_short_mask] -= unit[add_short_mask]

    # 做多：加仓（包括之前是多仓或空仓时直接加）
    new_position[long_mask] += unit[long_mask]

    return new_position

    # resultPosition = np.zeros(n_inst)
    # if np.any(all_signals == -1):
    #     signal = -1 * np.ones(n_inst)
    #     resultPosition = (signal * dollar_limit / last_prices).astype(int)
    # elif np.any(all_signals == 1):
    #     signal = 1 * np.ones(n_inst)
    #     resultPosition = (signal * dollar_limit / last_prices).astype(int)
    # else:
    #     resultPosition = currentPos
    # return resultPosition

#####################################################################################
# Update trading logs
#####################################################################################

def update_trading_logs(prcSoFar: np.ndarray):
    """
    Update the trading logs based on the current position and prices.
    """
    global position_history, currentPos

    # Update the position history
    update_position_history(prcSoFar)
    # Update NAV history
    update_nav_history(prcSoFar)

def update_nav_history(prcSoFar: np.ndarray):
    """
    Update the NAV history based on the current position and prices.
    """
    global nav_history, position_history
    # Initialize nav_history if it is None
    if nav_history is None:
        nav_history = np.array([])

    # Calculate the NAV value based on the current position
    last_prices = prcSoFar[:, -1]
    last_position = position_history[:, -1]
    nav_value = np.sum(last_position * last_prices)

    # Update the NAV history
    nav_history = np.append(nav_history, nav_value)

def update_position_history(prcSoFar: np.ndarray):
    """
    Update the position history based on the current position.
    """
    global position_history, currentPos
    # If position_history is None, initialize it
    if position_history is None:
        position_history = np.empty((prcSoFar.shape[0], 0))
    # Update the position history
    currentPos_col = currentPos.reshape(-1, 1)
    position_history = np.hstack((position_history, currentPos_col))

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

#######################################################################################
# Return functions for history and signals
#######################################################################################

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

def get_trading_logs():
    """
    Get the trading logs including NAV and position history.
    """
    return {
        'nav_history': nav_history,
        'position_history': position_history
    }
import numpy as np
import pandas as pd

##### TODO #########################################
### IMPLEMENT 'getMyPosition' FUNCTION #############
### TO RUN, RUN 'eval.py' ##########################

nInst = 50
currentPos = np.zeros(nInst)

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


signals['5_20'] = pd.DataFrame(columns=range(nInst))
signals['30_60'] = pd.DataFrame(columns=range(nInst))
signals['30_180'] = pd.DataFrame(columns=range(nInst))
#####################################################


def getMyPosition(prcSoFar: np.ndarray) -> np.ndarray:
    # update the position based on the latest prices
    global currentPos, signals, ma_history, nav_history, position_history

    update_trading_logs(prcSoFar)

    update_ma_history(prcSoFar)
    update_ma_signal(prcSoFar)

    currentPos = ma_strategy(prcSoFar)

    return currentPos

def ma_strategy(prcSoFar: np.ndarray) -> np.ndarray:

    (n_inst, n_days) = prcSoFar.shape
    global currentPos, signals, ma_history

    final_signal = np.zeros(n_inst)
    for signal_key in signals.keys():
        final_signal += signals[signal_key].iloc[-1].values

    # Update current position based on the signal
    # Use last day prices to estimate the postion
    last_prices = prcSoFar[:, -1]
    currentPos += final_signal * (cash_limit / last_prices).astype(int)

    pass
   
    
    return currentPos

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
        position_history = np.array([])
    # Update the position history
    position_history = np.append(position_history, currentPos)

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
import numpy as np

##### TODO #########################################
### IMPLEMENT 'getMyPosition' FUNCTION #############
### TO RUN, RUN 'eval.py' ##########################

nInst = 50


def getMyPosition(prcSoFar: np.ndarray) -> np.ndarray:
    # update the position based on the latest prices
    currentPos = ma2_strategy(prcSoFar, short_window=5, long_window=20, dollar_limit=8000)
    
    return currentPos

def ma2_strategy(prcSoFar: np.ndarray, short_window: int = 5, long_window: int = 20, dollar_limit: int = 8000) -> np.ndarray:

    # return if there are not enough days of data
    (n_inst, n_days) = prcSoFar.shape
    if n_days < long_window:
        return np.zeros(n_inst)
    
    cur_price = prcSoFar[:, -1]
    
    # Calculate the moving average
    cur_ma_short = np.mean(prcSoFar[:, -short_window:], axis=1)
    cur_ma_long = np.mean(prcSoFar[:, -long_window:], axis=1)
    
    signal = np.where(cur_ma_short > cur_ma_long, 1,
              np.where(cur_ma_short < cur_ma_long, -1, 0))

    # 按照 dollar_limit 分配股数
    position = (signal * dollar_limit / cur_price).astype(int)

    return position


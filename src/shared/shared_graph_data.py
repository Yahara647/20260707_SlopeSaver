# shared/shared_graph_data.py
from threading import Lock
from typing import Optional
import numpy as np


class SharedGraphData:
    def __init__(self):
        self.lock = Lock()

        # 実空間の赤輝点（world座標）
        self.red_in_world: Optional[np.ndarray] = None

        # 一次残差の最小値補正 residuals (shape=(N,2))
        self.slope_linear_residuals_min_adjusted: Optional[np.ndarray] = None


shared_graph_data = SharedGraphData()

# shared/shared_graph_data.py
from threading import Lock
from typing import Optional
import numpy as np


class SharedGraphData:
    def __init__(self):
        self.lock = Lock()

        # 実空間の赤輝点（world座標）
        self.red_in_world: Optional[np.ndarray] = None

        # slit_frame_adjusted_linear_residuals（shape=(N,2)）
        # GUI グラフの縦軸には [:, 0] を使用する。
        self.slit_frame_adjusted_linear_residuals: Optional[np.ndarray] = None


shared_graph_data = SharedGraphData()

from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np


class ICalibrationUI(ABC):
    """
    キャリブレーション UI の抽象インターフェース。
    """

    @abstractmethod
    def get_calibration_points(
        self,
        image: np.ndarray
    ) -> tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        """
        UI を表示し、pixel/world 座標を返す。
        """
        pass

from dataclasses import dataclass
import numpy as np
from datetime import datetime

@dataclass
class Rgb8Frame:
    """
    RGB8 (uint8, 3ch) の画像フレームを保持する構造体。
    """

    data: np.ndarray
    timestamp: datetime

    @classmethod
    def create(cls, data, timestamp):
        if not isinstance(data, np.ndarray):
            return None
        if data.ndim != 3:
            return None
        if data.shape[2] != 3:
            return None
        if data.dtype != np.uint8:
            return None
        if not isinstance(timestamp, datetime):
            return None

        return cls(data=data, timestamp=timestamp)

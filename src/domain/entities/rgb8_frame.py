from dataclasses import dataclass
import numpy as np
from datetime import datetime

@dataclass
class Rgb8Frame:
    """
    モノクロ画像（uint8, 2ch ではなく HxW の 2D 配列）を保持する構造体。
    既存のカラー用コードはこの移行期間に合わせて grayscale 前提へ統一する。
    """

    data: np.ndarray
    timestamp: datetime

    @classmethod
    def create(cls, data, timestamp):
        if not isinstance(data, np.ndarray):
            return None
        if data.ndim != 2:
            return None
        if data.dtype != np.uint8:
            return None
        if not isinstance(timestamp, datetime):
            return None

        return cls(data=data, timestamp=timestamp)

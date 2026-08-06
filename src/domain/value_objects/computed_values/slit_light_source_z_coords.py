from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SlitLightSourceZCoords:
    """
    スリット光源の実空間 z 座標群を保持する ValueObject。

    各要素は、画像内で検出されたスリット光点に対応する
    スリット光源の z 座標（LED y-z マッピングから取得）を表す。

    - values: shape = (N,), dtype = float32
    """

    values: np.ndarray  # shape = (N,), float32

    @property
    def is_empty(self) -> bool:
        return self.values is None or len(self.values) == 0

    @classmethod
    def create(cls, values: np.ndarray) -> "SlitLightSourceZCoords | bool":
        """
        安全なファクトリメソッド。shape=(N,) の float 配列のみ受け付ける。
        """
        if not isinstance(values, np.ndarray):
            return False
        if values.ndim != 1:
            return False
        return cls(values=values.astype(np.float32))

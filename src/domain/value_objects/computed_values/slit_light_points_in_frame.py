from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SlitLightPointsInFrame:
    """
    画像内で検出されたスリット光の点群（画像座標のみ）を保持するドメインモデル。

    光源 z 座標は SlitLightSourceZCoords として分離している。

    - coords_in_frame: 画像座標 (x, y)
                       shape = (N, 2), dtype = int32
                       各行が (x, y) を表す
    """

    coords_in_frame: np.ndarray  # shape = (N, 2), int32

    @property
    def is_empty(self) -> bool:
        """点が1つも検出されていない場合に True を返す。"""
        return self.coords_in_frame is None or len(self.coords_in_frame) == 0

    @classmethod
    def create(cls, coords_in_frame: np.ndarray) -> "SlitLightPointsInFrame | bool":
        """
        スリット光点を安全に生成するファクトリメソッド。

        Parameters
        ----------
        coords_in_frame : np.ndarray
            画像座標、shape=(N, 2), dtype=int32
        """
        if not isinstance(coords_in_frame, np.ndarray):
            return False
        if coords_in_frame.dtype != np.int32:
            return False
        if coords_in_frame.ndim != 2 or coords_in_frame.shape[1] != 2:
            return False
        return cls(coords_in_frame=coords_in_frame.copy())

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SingleBrightPointInFrame:
    """
    画像内で検出された「赤色の明るい点（単一点）」を保持するドメインモデル。

    - coord_in_frame: shape = (1, 2), dtype = int32
                      (x, y) の 1 点のみを保持する。
    """

    coord_in_frame: np.ndarray  # shape = (1, 2), int32

    @classmethod
    def create(cls, coord_in_frame: np.ndarray) -> "SingleBrightPointInFrame | False":
        """
        coord_in_frame を安全に格納するファクトリメソッド。
        型チェック・shape チェックを行い、異常時は False を返す。

        - coord_in_frame: NumPy ndarray, shape=(1,2), dtype=int32
        """

        # --- 型チェック ---
        if not isinstance(coord_in_frame, np.ndarray):
            return False

        # --- dtype チェック ---
        if coord_in_frame.dtype != np.int32:
            return False

        # --- shape チェック ---
        if coord_in_frame.ndim != 2 or coord_in_frame.shape != (1, 2):
            return False

        # ValueObject の不変性を守るためコピーして保持
        return cls(coord_in_frame=coord_in_frame.copy())

from dataclasses import dataclass
import numpy as np

@dataclass
class StripSlopes:
    """
    1フレーム分の傾斜角（slope_x, slope_y）を保持するドメイン。

    - slopes_in_world: 傾斜角の集合（np.ndarray, shape=(N, 2)）
                       各行が (slope_x_deg, slope_y_deg) を表す。
    """

    slopes_in_world: np.ndarray

    @classmethod
    def create(cls, slopes_in_world):
        """
        StripSlopes を安全に生成するファクトリメソッド。
        型チェック・shape チェックを行い、異常時は False を返す。

        - slopes_in_world: np.ndarray, shape=(N, 2)
        """

        # --- ndarray チェック ---
        if not isinstance(slopes_in_world, np.ndarray):
            return False

        # --- shape チェック ---
        if slopes_in_world.ndim != 2:
            return False
        if slopes_in_world.shape[1] != 2:
            return False

        return cls(slopes_in_world=slopes_in_world)

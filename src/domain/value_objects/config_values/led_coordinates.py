from dataclasses import dataclass
import numpy as np

@dataclass
class LedCoordinates:
    """
    複数の LED の世界座標を保持するドメインモデル。

    - coord_in_world: LED の世界座標を格納する NumPy 配列
                      shape = (N, 3), dtype = float32/float64
                      各行が (x, y, z) の 3 次元座標を表す。
    """

    coords_in_world: np.ndarray  # shape = (N, 3)

    @classmethod
    def create(cls, coords_in_world):
        """
        coord_in_world を安全に格納するファクトリメソッド。
        型チェック・shape チェックを行い、異常時は False を返す。

        - coord_in_world: NumPy ndarray, shape=(N, 3), dtype=float32/float64
        """

        # --- ndarray チェック ---
        if not isinstance(coords_in_world, np.ndarray):
            return False

        # --- dtype チェック（float32/float64 のみ許可） ---
        if coords_in_world.dtype not in (np.float32, np.float64):
            return False

        # --- shape チェック ---
        if coords_in_world.ndim != 2 or coords_in_world.shape[1] != 3:
            return False

        # 正常ならインスタンス生成
        return cls(coords_in_world=coords_in_world)

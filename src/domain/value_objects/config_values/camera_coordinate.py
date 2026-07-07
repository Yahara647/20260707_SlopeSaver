from dataclasses import dataclass
import numpy as np

@dataclass
class CameraCoordinate:
    """
    カメラの世界座標を保持するドメインモデル。

    - coord_in_world: カメラの世界座標を格納する NumPy 配列
                      shape = (3,), dtype = float32/float64
                      (x, y, z) の 3 次元座標を表す。
    """

    coord_in_world: np.ndarray  # shape = (3,)

    @classmethod
    def create(cls, coord_in_world):
        """
        coord_in_world を安全に格納するファクトリメソッド。
        型チェック・shape チェックを行い、異常時は False を返す。

        - coord_in_world: NumPy ndarray, shape=(3,), dtype=float32/float64
        """

        # --- ndarray チェック ---
        if not isinstance(coord_in_world, np.ndarray):
            return False

        # --- dtype チェック（float32/float64 のみ許可） ---
        if coord_in_world.dtype not in (np.float32, np.float64):
            return False

        # --- shape チェック ---
        if coord_in_world.ndim != 1 or coord_in_world.shape[0] != 3:
            return False

        # 正常ならインスタンス生成
        return cls(coord_in_world=coord_in_world)

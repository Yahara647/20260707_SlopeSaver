from dataclasses import dataclass
import numpy as np

@dataclass
class RedBrightPointsInWorld:
    """
    画像内で検出された赤色点を「実空間座標系」で保持するドメインモデル。

    - coords_in_world: 赤色点の世界座標を格納する NumPy 配列
                       shape = (N, 3)
                       各行が (x, y, z) 座標を表す。
    """

    coords_in_world: np.ndarray  # shape = (N, 3)

    @classmethod
    def create(cls, coords_in_world):
        """
        coords_in_world を安全に格納するファクトリメソッド。
        型チェック・shape チェックを行い、異常時は False を返す。

        - coords_in_world: NumPy ndarray, shape=(N,3)
        """

        # --- coords_in_world の型チェック ---
        if not isinstance(coords_in_world, np.ndarray):
            return False

        # --- shape チェック ---
        if coords_in_world.ndim != 2:
            return False
        if coords_in_world.shape[1] != 3:
            return False

        # 正常ならインスタンス生成
        return cls(coords_in_world=coords_in_world)

    @property
    def is_empty(self) -> bool:
        """座標が 0 点なら True"""
        return self.coords_in_world.size == 0

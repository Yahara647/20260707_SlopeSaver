from dataclasses import dataclass
import numpy as np

@dataclass
class NormalVectors:
    """
    1フレーム分の法線ベクトルを保持するドメイン。

    - normals_in_world: 法線ベクトルの集合（np.ndarray, shape=(N, 3)）
                        各行が (nx, ny, nz) を表す。
    """

    normals_in_world: np.ndarray

    @classmethod
    def create(cls, normals_in_world):
        """
        NormalVectors を安全に生成するファクトリメソッド。
        型チェック・shape チェックを行い、異常時は False を返す。

        - normals_in_world: np.ndarray, shape=(N, 3)
        """

        # --- ndarray チェック ---
        if not isinstance(normals_in_world, np.ndarray):
            return False

        # --- shape チェック ---
        if normals_in_world.ndim != 2:
            return False
        if normals_in_world.shape[1] != 3:
            return False

        # 正常ならインスタンス生成
        return cls(normals_in_world=normals_in_world)

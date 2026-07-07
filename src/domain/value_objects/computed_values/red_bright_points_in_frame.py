from dataclasses import dataclass
import numpy as np

@dataclass
class RedBrightPointsInFrame:
    """
    画像内で検出された「赤色の明るい点（Red Bright Points）」を
    1フレーム分まとめて保持するドメインモデル。

    - coords_in_frame: 赤色点の画像座標を格納する NumPy 配列
                       shape = (N, 2), dtype = int32
                       各行が (x, y) 座標を表す。
    """

    coords_in_frame: np.ndarray  # shape = (N, 2), int32

    @property
    def is_empty(self) -> bool:
        """赤色点が1つも検出されていない場合に True を返す。"""
        return self.coords_in_frame is None or len(self.coords_in_frame) == 0

    @classmethod
    def create(cls, coords_in_frame):
        """
        coords_in_frame を安全に格納するファクトリメソッド。
        型チェック・shape チェックを行い、異常時は False を返す。

        - coords_in_frame: NumPy ndarray, shape=(N,2), dtype=int32
        """

        # --- coords_in_frame の型チェック ---
        if not isinstance(coords_in_frame, np.ndarray):
            return False

        # --- dtype チェック（int32 前提） ---
        if coords_in_frame.dtype != np.int32:
            return False

        # --- shape チェック ---
        if coords_in_frame.ndim != 2 or coords_in_frame.shape[1] != 2:
            return False

        # 正常ならインスタンス生成
        return cls(coords_in_frame=coords_in_frame)

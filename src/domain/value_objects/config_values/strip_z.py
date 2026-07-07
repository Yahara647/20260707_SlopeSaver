from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class StripZ:
    """
    帯鋼の Z 座標（高さ方向の位置）を保持するドメインモデル。

    - value: Z 座標を表す float 値
             dtype = float32 / float64 のみ許可
    """

    value: float  # Z 座標（単一値）

    @classmethod
    def create(cls, value):
        """
        Z 座標を安全に格納するファクトリメソッド。
        型チェックを行い、異常時は False を返す。

        - value: float32 / float64 のスカラー値
        """

        # --- NumPy スカラー or Python float チェック ---
        if isinstance(value, np.generic):  # NumPy スカラー
            if value.dtype not in (np.float32, np.float64):
                return False
            return cls(value=float(value))

        # --- Python float チェック ---
        if isinstance(value, float):
            return cls(value=value)

        # --- int は許可しない（暗黙変換を避けるため） ---
        return False

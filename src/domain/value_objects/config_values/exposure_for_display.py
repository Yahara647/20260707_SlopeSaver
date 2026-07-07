from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class ExposureForDisplay:
    """
    表示用画像を撮像する際の露光時間を保持する ValueObject。

    - value: 露光時間（float32 / float64 のみ許可）
    """

    value: float

    @classmethod
    def create(cls, value):
        """
        露光時間を安全に格納するファクトリメソッド。
        float32 / float64 のみ許可し、異常時は False を返す。
        """

        # --- NumPy スカラーの場合（int/float をすべて受け付ける）---
        if isinstance(value, np.generic):
            return cls(value=float(value))

        # --- Python の float の場合 ---
        if isinstance(value, float):
            return cls(value=value)

        # --- Python の int の場合 ---
        if isinstance(value, int):
            return cls(value=float(value))

        return False

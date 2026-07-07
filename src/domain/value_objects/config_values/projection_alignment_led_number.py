from dataclasses import dataclass
import numpy as np

@dataclass(frozen=False)
class ProjectionAlignmentLedNumber:
    """
    投影LEDの位置合わせに使用する LED 番号を保持する ValueObject。

    - value: LED 番号（int32 のみ許可）
    """

    value: int

    @classmethod
    def create(cls, value):
        """
        LED 番号を安全に格納するファクトリメソッド。
        int32 のみ許可し、異常時は False を返す。
        """

        # NumPy スカラーの場合
        if isinstance(value, np.generic):
            if value.dtype != np.int32:
                return False
            return cls(value=int(value))

        # Python int の場合
        if isinstance(value, int):
            return cls(value=value)

        return False

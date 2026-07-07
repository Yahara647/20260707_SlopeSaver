from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class LedReflectionArea:
    """
    LED が帯鋼に投影され、画像上で明るく見える領域（ROI）を表す不変クラス。

    - x, y: ROI 左上座標（ピクセル）
    - width, height: ROI の幅と高さ（ピクセル）
    - Basler カメラの ROI 設定にそのまま渡すことを想定
    - 値はキャリブレーションで決定され、基本的に不変
    """

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self):
        """
        型チェックと値チェックを行う。
        dataclass(frozen=True) のため object.__setattr__ を使用。
        """

        # --- 型チェック ---
        if not isinstance(self.x, int):
            raise TypeError(f"x must be int, got {type(self.x)}")
        if not isinstance(self.y, int):
            raise TypeError(f"y must be int, got {type(self.y)}")
        if not isinstance(self.width, int):
            raise TypeError(f"width must be int, got {type(self.width)}")
        if not isinstance(self.height, int):
            raise TypeError(f"height must be int, got {type(self.height)}")

        # --- 値チェック ---
        if self.width <= 0:
            raise ValueError(f"width must be > 0, got {self.width}")
        if self.height <= 0:
            raise ValueError(f"height must be > 0, got {self.height}")
        if self.x < 0:
            raise ValueError(f"x must be >= 0, got {self.x}")
        if self.y < 0:
            raise ValueError(f"y must be >= 0, got {self.y}")

        # Basler の ROI increment に合わせた丸めは CameraControlService 側で行うため、
        # このクラスでは行わない（純粋なドメイン値として保持する）

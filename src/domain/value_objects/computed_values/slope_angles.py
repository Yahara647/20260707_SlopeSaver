from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SlopeAngles:
    """
    法線ベクトルから算出された X・Y 方向の勾配角度を保持する ValueObject。

    - slopes_in_world: shape = (N, 2)
                       各行が [x_slope_deg, y_slope_deg]
    """

    slopes_in_world: np.ndarray  # shape=(N,2)

    @property
    def is_empty(self) -> bool:
        return self.slopes_in_world is None or len(self.slopes_in_world) == 0

    @classmethod
    def create(cls, slopes_in_world: np.ndarray) -> "SlopeAngles | False":
        if not isinstance(slopes_in_world, np.ndarray):
            return False
        if slopes_in_world.ndim != 2 or slopes_in_world.shape[1] != 2:
            return False
        return cls(slopes_in_world=slopes_in_world.copy())

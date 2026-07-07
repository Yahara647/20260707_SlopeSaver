from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class LedWorldCoordinatesInFrame:
    """
    LED 番号に対応する世界座標を保持する ValueObject。

    - coords_in_world: shape = (N, 3), dtype=float32/float64
    """

    coords_in_world: np.ndarray

    @property
    def is_empty(self) -> bool:
        return self.coords_in_world is None or len(self.coords_in_world) == 0

    @classmethod
    def create(cls, coords_in_world: np.ndarray) -> "LedWorldCoordinatesInFrame | False":
        if not isinstance(coords_in_world, np.ndarray):
            return False
        if coords_in_world.ndim != 2 or coords_in_world.shape[1] != 3:
            return False
        return cls(coords_in_world=coords_in_world.copy())

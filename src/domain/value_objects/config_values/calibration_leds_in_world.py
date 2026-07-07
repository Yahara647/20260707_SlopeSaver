# src/domain/value_objects/computed_values/calibration_leds_in_world.py

from dataclasses import dataclass
import numpy as np

@dataclass
class CalibrationLedsInWorld:
    coords_in_world: np.ndarray  # shape = (N, 3), dtype=float64

    @classmethod
    def create(cls, coords: np.ndarray):
        if not isinstance(coords, np.ndarray):
            return False
        if coords.ndim != 2 or coords.shape[1] != 3:
            return False
        if coords.dtype not in (np.float32, np.float64, np.int32, np.int64):
            return False

        coords = coords.astype(np.float64)

        return cls(coords_in_world=coords)

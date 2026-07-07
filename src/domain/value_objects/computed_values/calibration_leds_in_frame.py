# src/domain/value_objects/computed_values/calibration_leds_in_frame.py

from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class CalibrationLedsInFrame:
    coords_in_frame: np.ndarray  # shape = (N, 2), dtype=float64

    @classmethod
    def create(cls, coords: np.ndarray):
        if not isinstance(coords, np.ndarray):
            return False
        if coords.ndim != 2 or coords.shape[1] != 2:
            return False
        if coords.dtype not in (np.float32, np.float64, np.int32, np.int64):
            return False

        # float64 に統一
        coords = coords.astype(np.float64)

        return cls(coords_in_frame=coords)

# src/domain/value_objects/evaluation_values/slope_slit_frame_adjusted_linear_residuals.py

from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SlopeSlitFrameAdjustedLinearResiduals:
    """
    スリット画像座標の一次近似差を用いて補正した一次残差を保持する ValueObject。
    """

    residuals: np.ndarray  # shape=(N,2)

    @property
    def is_empty(self) -> bool:
        return self.residuals is None or len(self.residuals) == 0

    @classmethod
    def create(cls, residuals: np.ndarray) -> "SlopeSlitFrameAdjustedLinearResiduals | False":
        if not isinstance(residuals, np.ndarray):
            return False
        if residuals.ndim != 2 or residuals.shape[1] != 2:
            return False
        return cls(residuals=residuals.copy())

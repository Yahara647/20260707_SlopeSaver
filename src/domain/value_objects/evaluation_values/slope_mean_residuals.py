from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SlopeMeanResiduals:
    """
    SlopeAngles の slope_x / slope_y を平均値と比較した際の
    残差（residuals）を保持する ValueObject。

    - residuals: shape = (N, 2)
                 各行が [residual_x, residual_y]
    """

    residuals: np.ndarray  # shape=(N,2)

    @property
    def is_empty(self) -> bool:
        return self.residuals is None or len(self.residuals) == 0

    @classmethod
    def create(cls, residuals: np.ndarray) -> "SlopeMeanResiduals | False":
        if not isinstance(residuals, np.ndarray):
            return False
        if residuals.ndim != 2 or residuals.shape[1] != 2:
            return False
        return cls(residuals=residuals.copy())

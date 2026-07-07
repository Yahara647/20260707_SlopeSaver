# src/domain/value_objects/evaluation_values/slope_linear_residuals.py

from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SlopeLinearResiduals:
    """
    SlopeAngles を world-y に対して一次近似した際の
    残差（residuals）を保持する ValueObject。

    - residuals: shape = (N, 2)
                 各行が [residual_x, residual_y]
    """

    residuals: np.ndarray  # shape=(N,2)

    @property
    def is_empty(self) -> bool:
        return self.residuals is None or len(self.residuals) == 0

    @classmethod
    def create(cls, residuals: np.ndarray) -> "SlopeLinearResiduals | False":
        """
        残差配列を安全に格納するファクトリメソッド。
        型チェック・shape チェックを行い、異常時は False を返す。

        - residuals: NumPy ndarray, shape=(N,2)
        """

        if not isinstance(residuals, np.ndarray):
            return False

        if residuals.ndim != 2 or residuals.shape[1] != 2:
            return False

        return cls(residuals=residuals.copy())

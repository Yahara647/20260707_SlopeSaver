# src/domain/value_objects/computed_values/homography_matrix.py

from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class HomographyMatrix:
    """
    ホモグラフィ行列 H（3×3）を保持する ValueObject。
    """

    matrix: np.ndarray  # shape = (3, 3), dtype=float64

    @classmethod
    def create(cls, matrix):
        if not isinstance(matrix, np.ndarray):
            return False
        if matrix.shape != (3, 3):
            return False
        if matrix.dtype not in (np.float32, np.float64):
            return False
        return cls(matrix=matrix)

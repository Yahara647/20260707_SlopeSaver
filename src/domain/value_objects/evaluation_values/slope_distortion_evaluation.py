from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class SlopeDistortionEvaluation:
    """
    歪み量評価を保持する ValueObject。

    - slope_score: 歪み量（linear_min_adjusted の第一成分の最大値）
    - slope_score_index: 最大歪み点の index
    """

    slope_score: float
    slope_score_index: int

    @property
    def is_empty(self) -> bool:
        return self.slope_score is None

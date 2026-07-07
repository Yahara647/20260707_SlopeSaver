from __future__ import annotations
import json
from dataclasses import asdict, is_dataclass
import numpy as np

from domain.aggregates.measurement_evaluation_result import MeasurementEvaluationResult


class MeasurementEvaluationResultRepository:
    """
    MeasurementEvaluationResult を JSON 保存する Repository。
    numpy.ndarray を list に変換して保存する。
    """

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    def _convert(self, obj):
        """
        dataclass → dict → numpy.ndarray → list に変換する再帰処理
        """
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        if is_dataclass(obj):
            return {k: self._convert(v) for k, v in asdict(obj).items()}

        if isinstance(obj, dict):
            return {k: self._convert(v) for k, v in obj.items()}

        if isinstance(obj, (list, tuple)):
            return [self._convert(v) for v in obj]

        return obj

    def save(self, evaluation: MeasurementEvaluationResult) -> None:
        data = self._convert(evaluation)

        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

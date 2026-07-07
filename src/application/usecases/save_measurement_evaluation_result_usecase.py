# src/application/usecases/save_measurement_evaluation_result_usecase.py

from __future__ import annotations
from pathlib import Path
from datetime import datetime

from domain.aggregates.measurement_evaluation_result import MeasurementEvaluationResult
from application.repositories.measurement_evaluation_result_repository import (
    MeasurementEvaluationResultRepository,
)


class SaveMeasurementEvaluationResultUseCase:
    """
    MeasurementEvaluationResult を保存する UseCase。

    - base_dir/YYYYMMDD/
    - base_dir/YYYYMMDD/YYYYMMDD_HHMMSS_mmmm/
    - evaluation.json を保存
    """

    def __init__(self) -> None:
        pass

    def execute(
        self,
        base_dir: str,
        evaluation: MeasurementEvaluationResult,
    ) -> Path:

        base_path: Path = Path(base_dir)

        # --- 日付フォルダ（YYYYMMDD） ---
        date_str: str = datetime.now().strftime("%Y%m%d")
        date_dir: Path = base_path / date_str
        date_dir.mkdir(parents=True, exist_ok=True)

        # --- 時刻フォルダ（YYYYMMDD_HHMMSS_mmmm） ---
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-2]
        out_dir: Path = date_dir / timestamp
        out_dir.mkdir(parents=True, exist_ok=True)

        # --- 保存 ---
        MeasurementEvaluationResultRepository(str(out_dir / "evaluation.json")).save(evaluation)

        return out_dir

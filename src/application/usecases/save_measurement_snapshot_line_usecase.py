from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from application.mappers.recursive_mapper import to_dict_recursive
from application.repositories.measurement_snapshot_csv_repository import (
    MeasurementSnapshotCsvRepository,
)
from domain.aggregates.app_config import AppConfig
from domain.aggregates.calibration_preparation_result import CalibrationPreparationResult
from domain.aggregates.measurement_evaluation_result import MeasurementEvaluationResult
from domain.aggregates.projection_alignment_result import ProjectionAlignmentResult
from domain.aggregates.slope_computation_result import SlopeComputationResult


class SaveMeasurementSnapshotLineUseCase:
    """
    計測1回分のスナップショットを日次 CSV ファイルへ追記する UseCase。

    app_config.json / calib.json / proj.json / result.json / evaluation.json の
    末端要素を列として定義し、実行ごとに値行を1行追加する。
    """

    MAX_PATH_LEVELS = 8

    def _flatten_leaf_rows(
        self,
        source_file: str,
        value: Any,
        path: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        if path is None:
            path = []

        rows: list[dict[str, Any]] = []

        if isinstance(value, dict):
            for key, child in value.items():
                rows.extend(self._flatten_leaf_rows(source_file, child, path + [str(key)]))
            return rows

        if isinstance(value, list):
            for idx, child in enumerate(value):
                rows.extend(self._flatten_leaf_rows(source_file, child, path + [str(idx)]))
            return rows

        row: dict[str, Any] = {
            "source_file": source_file,
            "path_full": ".".join(path),
            "value": value,
        }

        for i in range(self.MAX_PATH_LEVELS):
            row[f"path_{i + 1}"] = path[i] if i < len(path) else ""

        rows.append(row)
        return rows

    def execute(
        self,
        base_dir: str,
        app_config: AppConfig,
        calib: CalibrationPreparationResult,
        proj: ProjectionAlignmentResult,
        slope: SlopeComputationResult,
        evaluation: MeasurementEvaluationResult,
    ) -> Path:
        date_str = datetime.now().strftime("%Y%m%d")
        out_path = Path(base_dir) / f"{date_str}.csv"
        saved_at = datetime.now().isoformat(timespec="milliseconds")

        entries: list[dict[str, Any]] = []
        entries.append(
            {
                "source_file": "_meta",
                "path_full": "saved_at",
                "path_1": "saved_at",
                "value": saved_at,
            }
        )
        entries.extend(self._flatten_leaf_rows("evaluation.json", to_dict_recursive(evaluation)))
        entries.extend(self._flatten_leaf_rows("result.json", to_dict_recursive(slope)))
        entries.extend(self._flatten_leaf_rows("app_config.json", to_dict_recursive(app_config)))
        entries.extend(self._flatten_leaf_rows("calib.json", to_dict_recursive(calib)))
        entries.extend(self._flatten_leaf_rows("proj.json", to_dict_recursive(proj)))

        repo = MeasurementSnapshotCsvRepository(str(out_path))
        repo.append_snapshot(entries)

        return out_path

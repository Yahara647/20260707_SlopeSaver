# src/application/usecases/save_measurement_results_usecase.py

from __future__ import annotations

from pathlib import Path
from datetime import datetime

from domain.aggregates.app_config import AppConfig
from domain.aggregates.calibration_preparation_result import CalibrationPreparationResult
from domain.aggregates.projection_alignment_result import ProjectionAlignmentResult
from domain.aggregates.slope_computation_result import SlopeComputationResult

from application.repositories.app_config_repository import AppConfigRepository
from application.repositories.calibration_preparation_result_repository import CalibrationPreparationResultRepository
from application.repositories.projection_alignment_result_repository import ProjectionAlignmentResultRepository
from application.repositories.slope_computation_result_repository import SlopeComputationResultRepository


class SaveMeasurementResultsUseCase:
    """
    4つのアグリゲートをまとめて保存するユースケース。

    - execute() 呼び出し時に base_dir を指定する
    - base_dir/YYYYMMDD/ を作成
    - その中に YYYYMMDD_HHMMSS_mmmm/ を作成
    - app_config.json / calib.json / proj.json / result.json を保存
    """

    def __init__(self) -> None:
        pass

    def execute(
        self,
        base_dir: str,
        app_config: AppConfig,
        calib: CalibrationPreparationResult,
        proj: ProjectionAlignmentResult,
        slope: SlopeComputationResult,
    ) -> Path:
        """
        計測結果をまとめて保存し、作成したフォルダのパスを返す。
        """

        base_path: Path = Path(base_dir)

        # --- 日付フォルダ（YYYYMMDD） ---
        date_str: str = datetime.now().strftime("%Y%m%d")
        date_dir: Path = base_path / date_str
        date_dir.mkdir(parents=True, exist_ok=True)

        # --- 時刻フォルダ（YYYYMMDD_HHMMSS_mmmm） ---
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-2]
        out_dir: Path = date_dir / timestamp
        out_dir.mkdir(parents=True, exist_ok=True)

        # --- Repository を使って保存 ---
        AppConfigRepository(str(out_dir / "app_config.json")).save(app_config)
        CalibrationPreparationResultRepository(str(out_dir / "calib.json")).save(calib)
        ProjectionAlignmentResultRepository(str(out_dir / "proj.json")).save(proj)
        SlopeComputationResultRepository(str(out_dir / "result.json")).save(slope)

        return out_dir

import json
import sys
from pathlib import Path

sys.path.append(str(Path("src").resolve()))

from application.mappers.recursive_mapper import from_dict_recursive
from application.repositories.app_config_repository import AppConfigRepository
from application.repositories.calibration_preparation_result_repository import CalibrationPreparationResultRepository
from application.repositories.projection_alignment_result_repository import ProjectionAlignmentResultRepository
from application.repositories.slope_computation_result_repository import SlopeComputationResultRepository
from application.usecases.save_measurement_snapshot_line_usecase import SaveMeasurementSnapshotLineUseCase
from domain.aggregates.measurement_evaluation_result import MeasurementEvaluationResult


def collect_run_dirs(base: Path) -> list[Path]:
    out: list[Path] = []
    if not base.exists():
        return out

    for date_dir in base.iterdir():
        if not date_dir.is_dir():
            continue
        for run_dir in date_dir.iterdir():
            if run_dir.is_dir():
                out.append(run_dir)

    out.sort(reverse=True)
    return out


root = Path("output")
result_candidates = collect_run_dirs(root / "results")
eval_candidates = collect_run_dirs(root / "evaluation_results")

result_dir = next(
    (
        p
        for p in result_candidates
        if (p / "app_config.json").exists()
        and (p / "calib.json").exists()
        and (p / "proj.json").exists()
        and (p / "result.json").exists()
    ),
    None,
)

eval_dir = next(
    (
        p
        for p in eval_candidates
        if (p / "evaluation.json").exists()
    ),
    None,
)

if result_dir is None or eval_dir is None:
    raise RuntimeError("required files not found")

app_config = AppConfigRepository(str(result_dir / "app_config.json")).load()
calib = CalibrationPreparationResultRepository(str(result_dir / "calib.json")).load()
proj = ProjectionAlignmentResultRepository(str(result_dir / "proj.json")).load()
slope = SlopeComputationResultRepository(str(result_dir / "result.json")).load()
with open(eval_dir / "evaluation.json", "r", encoding="utf-8") as f:
    evaluation_data = json.load(f)
evaluation = from_dict_recursive(MeasurementEvaluationResult, evaluation_data)

out_path = SaveMeasurementSnapshotLineUseCase().execute(
    base_dir="output/daily_snapshots",
    app_config=app_config,
    calib=calib,
    proj=proj,
    slope=slope,
    evaluation=evaluation,
)

print("generated=" + str(out_path))
print("from_result=" + str(result_dir))
print("from_eval=" + str(eval_dir))

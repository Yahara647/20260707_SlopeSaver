import json
from domain.aggregates.calibration_preparation_result import CalibrationPreparationResult
from application.mappers.recursive_mapper import to_dict_recursive, from_dict_recursive


class CalibrationPreparationResultRepository:

    def __init__(self, path: str):
        self.path = path

    def load(self) -> CalibrationPreparationResult:
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return from_dict_recursive(CalibrationPreparationResult, data)

    def save(self, result: CalibrationPreparationResult):
        data = to_dict_recursive(result)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

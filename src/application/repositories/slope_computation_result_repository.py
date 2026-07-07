# src/application/repositories/slope_computation_result_repository.py

import json
from domain.aggregates.slope_computation_result import SlopeComputationResult
from application.mappers.recursive_mapper import to_dict_recursive, from_dict_recursive


class SlopeComputationResultRepository:

    def __init__(self, path: str):
        self.path = path

    def load(self) -> SlopeComputationResult:
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return from_dict_recursive(SlopeComputationResult, data)

    def save(self, result: SlopeComputationResult):
        data = to_dict_recursive(result)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

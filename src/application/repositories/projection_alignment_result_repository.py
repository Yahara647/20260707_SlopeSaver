# src/application/repositories/projection_alignment_result_repository.py

import json
from domain.aggregates.projection_alignment_result import ProjectionAlignmentResult
from application.mappers.recursive_mapper import to_dict_recursive, from_dict_recursive


class ProjectionAlignmentResultRepository:

    def __init__(self, path: str):
        self.path = path

    def load(self) -> ProjectionAlignmentResult:
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return from_dict_recursive(ProjectionAlignmentResult, data)

    def save(self, result: ProjectionAlignmentResult):
        data = to_dict_recursive(result)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

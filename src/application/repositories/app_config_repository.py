import json
from domain.aggregates.app_config import AppConfig
from application.mappers.recursive_mapper import to_dict_recursive, from_dict_recursive


class AppConfigRepository:

    def __init__(self, path: str):
        self.path = path

    def load(self) -> AppConfig:
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return from_dict_recursive(AppConfig, data)

    def save(self, config: AppConfig):
        data = to_dict_recursive(config)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

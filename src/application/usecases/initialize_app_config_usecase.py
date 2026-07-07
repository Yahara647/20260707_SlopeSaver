# src/application/usecases/initialize_app_config_usecase.py

from domain.aggregates.app_config import AppConfig
from application.repositories.app_config_repository import AppConfigRepository


class InitializeAppConfigUseCase:
    """
    AppConfig を初期化する UseCase。

    - 設定ファイルを読み込み
    - recursive_mapper により AppConfig に復元し
    - 呼び出し元に返す

    ※ AppConfig の生成ロジックは Repository + Mapper に委譲する。
    """

    def __init__(self, repository: AppConfigRepository):
        self._repository = repository

    def execute(self) -> AppConfig:
        """
        AppConfig を JSON から読み込み、復元して返す。
        """
        return self._repository.load()

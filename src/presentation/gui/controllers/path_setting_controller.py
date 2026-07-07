# src/presentation/gui/controllers/path_setting_controller.py

from __future__ import annotations

from domain.aggregates.app_config import AppConfig
from infrastructure.camera.pylon_camera_driver import PylonCameraDriver
from infrastructure.dio.dio_led_driver import DioLedDriver


class PathSettingController:
    """
    PathSettingView の操作を受け取るが、
    現段階では何の処理も行わない最小構成のコントローラ。
    """

    def __init__(
        self,
        config: AppConfig,
        camera_service: PylonCameraDriver,
        dio_service: DioLedDriver,
    ) -> None:
        self.config = config
        self.camera_service = camera_service
        self.dio_service = dio_service

    # ---------------------------------------------------------
    # パス設定適用（まだ何もしない）
    # ---------------------------------------------------------
    def on_apply_paths(self, save_dir: str, config_dir: str) -> None:
        """
        PathSettingView から保存先フォルダと設定フォルダが渡されるが、
        現段階では何も処理しない。
        後で UseCase を適用するためのフック。
        """
        pass

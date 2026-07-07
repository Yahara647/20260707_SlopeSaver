# src/application/services/camera/camera_capture_service.py

from domain.interfaces.i_camera_service import ICameraService
from infrastructure.camera.camera_state import CameraState
from logging import Logger
from domain.entities.rgb8_frame import Rgb8Frame


class CameraCaptureService:
    def __init__(self, camera_service: ICameraService, camera_state: CameraState, logger: Logger):
        self.camera_service = camera_service
        self.camera_state = camera_state
        self.logger = logger

    def capture_once(self) -> Rgb8Frame | None:
        """
        通常露光で1枚撮像する。
        """
        if not self.camera_state.is_initialized:
            self.logger.error("CaptureService: カメラが初期化されていません")
            return None

        try:
            frame: Rgb8Frame | None = self.camera_service.capture()

            if frame is None:
                self.logger.error("CaptureService: 撮像失敗")
                return None

            return frame

        except Exception:
            self.logger.exception("CaptureService: 撮像中に例外発生")
            return None

    # ---------------------------------------------------------
    # ★ 新規追加：露光変更＋撮像（排他ロック内で一括実行）
    # ---------------------------------------------------------
    def capture_with_exposure(self, exposure_us: float) -> Rgb8Frame | None:
        """
        指定露光で1枚撮像し、撮像後に元の露光に戻す。
        PylonCameraDriver の capture_with_exposure() をそのまま呼ぶ。
        """
        if not self.camera_state.is_initialized:
            self.logger.error("CaptureService: カメラが初期化されていません")
            return None

        try:
            frame = self.camera_service.capture_with_exposure(exposure_us)

            if frame is None:
                self.logger.error("CaptureService: capture_with_exposure() による撮像失敗")
                return None

            return frame

        except Exception:
            self.logger.exception("CaptureService: capture_with_exposure() 中に例外発生")
            return None

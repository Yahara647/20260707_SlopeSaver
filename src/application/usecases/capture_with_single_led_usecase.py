from application.services.led.led_control_service import LedControlService
from application.services.camera.camera_capture_service import CameraCaptureService
from application.services.led.led_stabilize_service import LedStabilizeService
from logging import Logger
import numpy as np


class CaptureWithSingleLedUseCase:

    def __init__(
        self,
        led_service: LedControlService,
        camera_service: CameraCaptureService,
        stabilize_service: LedStabilizeService,
        logger: Logger
    ):
        self.led_service = led_service
        self.camera_service = camera_service
        self.stabilize_service = stabilize_service
        self.logger = logger

    def execute(self, led_id: int) -> np.ndarray | None:
        self.logger.info(f"UseCase: LED {led_id} を点灯して撮像開始（Single LED）")

        # --- LED ON ---
        if not self.led_service.turn_only(led_id):
            self.logger.error("UseCase: LED 点灯に失敗")
            return None

        # --- LED 安定待ち（0.15 秒） ---
        self.stabilize_service.wait_until_stable(led_id)

        # --- 撮像 ---
        frame = self.camera_service.capture_once()
        if frame is None:
            self.logger.error("UseCase: 撮像に失敗")
            return None

        self.logger.info("UseCase: 撮像成功（LED は点灯したまま）")

        return frame

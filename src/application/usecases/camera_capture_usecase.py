from application.services.camera.camera_capture_service import CameraCaptureService
from logging import Logger
import numpy as np


class CameraCaptureUseCase:
    def __init__(self, capture_service: CameraCaptureService, logger: Logger):
        self.capture_service = capture_service
        self.logger = logger

    def execute(self) -> np.ndarray | None:
        self.logger.info("UseCase: カメラ撮像開始")
        return self.capture_service.capture_once()

from logging import Logger
from application.services.camera.camera_control_service import CameraControlService


class SetRoiUseCase:

    def __init__(self, control_service: CameraControlService, logger: Logger):
        self.control_service = control_service
        self.logger = logger

    def execute(self, x: int, y: int, width: int, height: int) -> bool:
        self.logger.info(f"UseCase: ROI 設定 x={x}, y={y}, w={width}, h={height}")
        return self.control_service.set_roi(x, y, width, height)

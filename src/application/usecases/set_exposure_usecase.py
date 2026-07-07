from logging import Logger
from application.services.camera.camera_control_service import CameraControlService


class SetExposureUseCase:

    def __init__(
        self,
        control_service: CameraControlService,
        logger: Logger
    ) -> None:
        self.control_service = control_service
        self.logger = logger

    def execute(self, exposure_us: float) -> bool:
        return self.control_service.set_exposure(exposure_us)

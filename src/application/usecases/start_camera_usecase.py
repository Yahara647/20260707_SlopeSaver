from domain.interfaces.i_camera_service import ICameraService
from infrastructure.camera.camera_state import CameraState
from logging import Logger


class StartCameraUseCase:
    def __init__(
        self,
        camera_service: ICameraService,
        camera_state: CameraState,
        logger: Logger
    ):
        self.camera_service = camera_service
        self.camera_state = camera_state
        self.logger = logger

    def execute(self) -> bool:
        self.logger.info("UseCase: カメラ起動開始")

        success = self.camera_service.initialize()
        self.camera_state.is_initialized = success

        if success:
            self.logger.info("UseCase: カメラ起動成功")
        else:
            self.logger.error("UseCase: カメラ起動失敗")

        return success

from logging import Logger
from infrastructure.camera.pylon_camera_driver import PylonCameraDriver
from infrastructure.camera.camera_state import CameraState


class CameraControlService:

    def __init__(
        self,
        driver: PylonCameraDriver,
        state: CameraState,
        logger: Logger
    ) -> None:
        self.driver = driver
        self.state = state
        self.logger = logger

    def get_exposure(self) -> float:
        """現在の露光時間を返す"""
        return self.state.exposure_time


    def set_exposure(self, exposure_us: float) -> bool:
        """露光時間を設定し、成功したら CameraState を更新し、捨てフレームを処理する"""

        # --- 露光設定 ---
        if not self.driver.set_exposure_time(exposure_us):
            return False

        # --- CameraState 更新 ---
        self.state.exposure_time = exposure_us

        # --- 捨てフレーム処理 ---
        self.logger.info("CameraControlService: 露光変更後の捨てフレーム処理を開始")

        for i in range(3):
            _ = self.driver.capture()
            self.logger.debug(f"捨てフレーム {i+1} 枚目")

        self.logger.info("CameraControlService: 捨てフレーム処理完了")

        return True
    
    def set_roi(self, x: int, y: int, width: int, height: int) -> bool:
        """ROI を設定し、成功したら CameraState を更新し、捨てフレームを処理する"""

        # --- Basler ace2 の制約に合わせて丸める ---
        x_rounded = (x // 32) * 32
        width_rounded = (width // 32) * 32

        y_rounded = (y // 16) * 16
        height_rounded = (height // 16) * 16

        self.logger.info(
            f"CameraControlService: ROI 丸め後 x={x_rounded}, y={y_rounded}, "
            f"w={width_rounded}, h={height_rounded}"
        )

        # --- ドライバに ROI 設定 ---
        if not self.driver.set_roi(x_rounded, y_rounded, width_rounded, height_rounded):
            self.logger.error("CameraControlService: ROI 設定に失敗しました")
            return False

        # --- CameraState 更新 ---
        self.state.roi_x = x_rounded
        self.state.roi_y = y_rounded
        self.state.roi_width = width_rounded
        self.state.roi_height = height_rounded

        # --- 捨てフレーム処理（絶対に消さない） ---
        self.logger.info("CameraControlService: ROI 変更後の捨てフレーム処理を開始")

        for i in range(3):
            _ = self.driver.capture()
            self.logger.debug(f"ROI 捨てフレーム {i+1} 枚目")

        self.logger.info("CameraControlService: ROI 捨てフレーム処理完了")

        return True

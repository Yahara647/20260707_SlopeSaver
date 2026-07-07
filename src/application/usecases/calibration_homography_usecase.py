from typing import List, Tuple
import numpy as np

from domain.entities.rgb8_frame import Rgb8Frame
from domain.value_objects.computed_values.calibration_leds_in_frame import CalibrationLedsInFrame
from domain.value_objects.config_values.calibration_leds_in_world import CalibrationLedsInWorld
from domain.value_objects.computed_values.homography_matrix import HomographyMatrix
from domain.services.homography_transformer import HomographyTransformer
from domain.interfaces.i_calibration_ui import ICalibrationUI

from application.services.camera.camera_capture_service import CameraCaptureService
from application.services.camera.camera_control_service import CameraControlService


class CalibrationHomographyUseCase:
    """
    露光設定 → 撮像 → 統合UI → Homography 計算 のユースケース。
    """

    def __init__(
        self,
        camera_capture_service: CameraCaptureService,
        camera_control_service: CameraControlService,
        homography_service: HomographyTransformer,
        calibration_ui: ICalibrationUI,
    ) -> None:
        self.camera_capture_service = camera_capture_service
        self.camera_control_service = camera_control_service
        self.homography_service = homography_service
        self.calibration_ui = calibration_ui

    def execute(self, exposure_us: float) -> HomographyMatrix:
        # --- 1. 露光設定 ---
        ok: bool = self.camera_control_service.set_exposure(exposure_us)
        if not ok:
            raise RuntimeError(f"露光設定に失敗しました: {exposure_us} us")

        # --- 2. カメラ撮像 ---
        frame: Rgb8Frame | None = self.camera_capture_service.capture_once()
        if frame is None:
            raise RuntimeError("撮像に失敗しました")

        # --- 3. 統合 UI（点選択 + 座標入力） ---
        pixel_points, world_points = self.calibration_ui.get_calibration_points(
            frame.data
        )

        # --- 4. ValueObject 化 ---
        calib_frame = CalibrationLedsInFrame.create(np.array(pixel_points))
        calib_world = CalibrationLedsInWorld.create(np.array(world_points))

        # --- 5. Homography 計算 ---
        H_vo: HomographyMatrix = self.homography_service.compute_homography(
            calib_in_frame=calib_frame,
            calib_in_world=calib_world
        )

        return H_vo


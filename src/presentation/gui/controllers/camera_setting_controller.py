# src/presentation/gui/controllers/camera_setting_controller.py

from __future__ import annotations

import multiprocessing
from multiprocessing import Process, Queue
import numpy as np

from domain.aggregates.app_config import AppConfig
from domain.aggregates.calibration_preparation_result import CalibrationPreparationResult

from domain.value_objects.computed_values.calibration_leds_in_frame import CalibrationLedsInFrame
from domain.value_objects.config_values.calibration_leds_in_world import CalibrationLedsInWorld
from domain.value_objects.config_values.led_reflection_area import LedReflectionArea
from domain.value_objects.config_values.exposure_for_display import ExposureForDisplay
from domain.value_objects.config_values.exposure_for_computation import ExposureForComputation

from infrastructure.camera.pylon_camera_driver import PylonCameraDriver
from infrastructure.dio.dio_led_driver import DioLedDriver

from domain.services.homography_transformer import HomographyTransformer
from infrastructure.ui.calibration_integrated_ui import CalibrationIntegratedUI

from logger.logger import logger


def _run_calibration_ui(queue: Queue, image: np.ndarray, initial_world_points: np.ndarray | None) -> None:
    ui = CalibrationIntegratedUI(initial_world_points=initial_world_points)
    pixel_points, world_points = ui.get_calibration_points(image)
    queue.put((pixel_points, world_points))


def _run_roi_ui(queue, image, initial_roi, max_w, max_h):
    from infrastructure.ui.roi_setting_ui import RoiSettingUI
    ui = RoiSettingUI(initial_roi=initial_roi, max_w=max_w, max_h=max_h)
    roi = ui.get_roi(image)
    queue.put(roi)


class CameraSettingController:
    """
    CameraSettingView の操作を受け取るコントローラ。
    """

    def __init__(
        self,
        config: AppConfig,
        camera_service: PylonCameraDriver,
        dio_service: DioLedDriver,
        calibration_preparation_result: CalibrationPreparationResult
    ) -> None:
        self.config = config
        self.camera_service = camera_service
        self.dio_service = dio_service
        self.calibration_preparation_result: CalibrationPreparationResult = calibration_preparation_result

    def on_apply_all_settings(self, display_exp: int, compute_exp: int) -> None:
        logger.info(f"ApplyAll: display={display_exp}, compute={compute_exp}")

        # 1. Camera に露光適用（表示用）
        ok_exp = self.camera_service.set_exposure_time(display_exp)
        if not ok_exp:
            logger.error("表示用露光の設定に失敗")
            return

        # # 2. Camera にゲイン適用
        # try:
        #     cam = self.camera_service.camera
        #     cam.GainAuto.SetValue("Off")
        #     cam.Gain.SetValue(gain)
        #     self.camera_service.state.gain = gain
        # except Exception as e:
        #     logger.error(f"ゲイン設定失敗: {e}")
        #     return

        # 3. AppConfig 更新（★ create() が False の場合は更新しない）
        new_display = ExposureForDisplay.create(display_exp)
        if new_display is False:
            logger.error("ExposureForDisplay.create() が False を返しました")
            return

        new_compute = ExposureForComputation.create(compute_exp)
        if new_compute is False:
            logger.error("ExposureForComputation.create() が False を返しました")
            return

        self.config.exposure_for_display = new_display
        self.config.exposure_for_computation = new_compute

        logger.info("ApplyAll: AppConfig の露光値を更新しました")



    # ---------------------------------------------------------
    # ★ Tkinter UI を別プロセスで起動してホモグラフィを導出
    # ---------------------------------------------------------
    def on_calibrate_homography(self, exposure_us: float = 5000.0) -> None:
        logger.info("CameraSettingController: ホモグラフィ導出処理を開始（別プロセス UI）")

        frame = self.camera_service.capture_with_exposure(exposure_us)
        if frame is None:
            logger.error("CameraSettingController: キャリブレーション用の画像が取得できませんでした")
            return

        image = frame.data

        initial_world_points = self.config.calibration_leds_in_world.coords_in_world

        queue: Queue = multiprocessing.Queue()
        p: Process = Process(
            target=_run_calibration_ui,
            args=(queue, image, initial_world_points)
        )
        p.start()
        p.join()

        if queue.empty():
            logger.error("CameraSettingController: キャリブレーション UI から座標が返されませんでした")
            return

        pixel_points, world_points = queue.get()
        logger.info(f"CameraSettingController: UI から取得 pixel={len(pixel_points)}, world={len(world_points)}")

        pixel_np = np.array(pixel_points, dtype=np.float64)
        world_np = np.array(world_points, dtype=np.float64)

        calib_in_frame = CalibrationLedsInFrame.create(pixel_np)
        if calib_in_frame is False:
            logger.error("CalibrationLedsInFrame の生成に失敗しました")
            return

        calib_in_world = CalibrationLedsInWorld.create(world_np)
        if calib_in_world is False:
            logger.error("CalibrationLedsInWorld の生成に失敗しました")
            return

        try:
            transformer = HomographyTransformer()
            H_vo = transformer.compute_homography(
                calib_in_frame=calib_in_frame,
                calib_in_world=calib_in_world
            )
        except Exception as e:
            logger.error(f"CameraSettingController: HomographyTransformer による計算に失敗: {e}")
            return

        self.calibration_preparation_result.calibration_leds_in_frame = calib_in_frame
        self.calibration_preparation_result.homography_matrix = H_vo
        self.config.calibration_leds_in_world = calib_in_world

        logger.info("CameraSettingController: ホモグラフィ行列の導出が完了")
        logger.info(f"H =\n{H_vo.matrix}")

    # ---------------------------------------------------------
    # ★ ROI 設定 UI を別プロセスで起動して ROI を更新
    # ---------------------------------------------------------
    def on_set_roi(self, exposure_us: float = 5000.0) -> None:
        logger.info("CameraSettingController: ROI 設定 UI を起動")

        # --- 現在の ROI を保存 ---
        current_roi = self.config.led_reflection_area
        orig_x, orig_y, orig_w, orig_h = (
            current_roi.x,
            current_roi.y,
            current_roi.width,
            current_roi.height,
        )
        logger.info(f"CameraSettingController: 現在の ROI = {current_roi}")

        # ---------------------------------------------------------
        # ★ 1. カメラ ROI を最大範囲に変更
        # ---------------------------------------------------------
        try:
            full_w, full_h = self.camera_service.get_max_resolution()
            logger.info(f"CameraSettingController: ROI をフルフレームに変更 → {full_w}x{full_h}")
            self.camera_service.set_roi(x=0, y=0, w=full_w, h=full_h)
        except Exception as e:
            logger.error(f"CameraSettingController: フルフレーム ROI 設定に失敗: {e}")
            return

        # ---------------------------------------------------------
        # ★ 2. フルフレーム画像を撮像
        # ---------------------------------------------------------
        frame = self.camera_service.capture_with_exposure(exposure_us)
        if frame is None:
            logger.error("CameraSettingController: ROI 用のフルフレーム画像が取得できませんでした")
            return

        full_image = frame.data

        # ---------------------------------------------------------
        # ★ 3. ROI を元に戻す
        # ---------------------------------------------------------
        try:
            self.camera_service.set_roi(x=orig_x, y=orig_y, w=orig_w, h=orig_h)
            logger.info("CameraSettingController: ROI を元に戻しました")
        except Exception as e:
            logger.error(f"CameraSettingController: ROI の復元に失敗: {e}")
            return

        # ---------------------------------------------------------
        # ★ 4. ROI UI を別プロセスで起動
        # ---------------------------------------------------------
        initial_roi = (orig_x, orig_y, orig_w, orig_h)

        queue: Queue = multiprocessing.Queue()
        p = Process(
            target=_run_roi_ui,
            args=(queue, full_image, initial_roi, full_w, full_h)
        )

        p.start()
        p.join()

        if queue.empty():
            logger.error("CameraSettingController: ROI UI から値が返されませんでした")
            return

        x, y, w, h = queue.get()
        logger.info(f"CameraSettingController: ROI UI から取得 → x={x}, y={y}, w={w}, h={h}")

        # ---------------------------------------------------------
        # ★ 5. AppConfig を更新
        # ---------------------------------------------------------
        try:
            new_roi = LedReflectionArea(x=x, y=y, width=w, height=h)
            self.config.led_reflection_area = new_roi
            logger.info(f"CameraSettingController: ROI を更新しました → {new_roi}")
        except Exception as e:
            logger.error(f"CameraSettingController: ROI の更新に失敗: {e}")
            return

        # ---------------------------------------------------------
        # ★ 6. カメラに新 ROI を適用
        # ---------------------------------------------------------
        try:
            self.camera_service.set_roi(x=x, y=y, w=w, h=h)
            logger.info("CameraSettingController: カメラに新 ROI を適用しました")
        except Exception as e:
            logger.error(f"CameraSettingController: カメラ ROI 設定に失敗: {e}")

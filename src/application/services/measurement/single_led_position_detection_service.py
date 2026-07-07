# src/application/services/measurement/single_led_position_detection_service.py

from __future__ import annotations
import numpy as np

from logger.logger import logger

# --- Interfaces ---
from domain.interfaces.i_camera_service import ICameraService
from domain.interfaces.i_led_driver import ILedDriver

# --- Application Services ---
from application.services.led.led_control_service import LedControlService
from application.services.camera.camera_control_service import CameraControlService
from application.services.camera.camera_capture_service import CameraCaptureService
from application.services.image_processing.red_light_detection_service import RedLightDetectionService

# --- ValueObjects ---
from domain.value_objects.config_values.projection_alignment_led_number import ProjectionAlignmentLedNumber
from domain.value_objects.config_values.exposure_for_computation import ExposureForComputation
from domain.value_objects.computed_values.single_bright_point_in_frame import SingleBrightPointInFrame

# --- DomainService ---
from domain.services.red_light_detector import RedLightDetector


class SingleLedPositionDetectionService:
    """
    指定した LED を 1 点だけ点灯し、
    capture_with_exposure() により露光変更＋撮像を排他で行い、
    輝点検出を行う Service。
    """

    def __init__(
        self,
        camera_service: ICameraService,
        led_driver: ILedDriver,
    ) -> None:

        self._logger = logger

        # --- Application Services（内部組み立て） ---
        self.led_control_service = LedControlService(
            led_driver=led_driver,
            logger=logger
        )

        self.camera_control_service = CameraControlService(
            driver=camera_service,
            state=camera_service.state,
            logger=logger
        )

        self.camera_capture_service = CameraCaptureService(
            camera_service=camera_service,
            camera_state=camera_service.state,
            logger=logger
        )

        detector = RedLightDetector()
        self.red_light_detection_service = RedLightDetectionService(detector)

    # ---------------------------------------------------------
    # LED の位置を推定するメイン処理
    # ---------------------------------------------------------
    def run(
        self,
        projection_alignment_led_number: ProjectionAlignmentLedNumber,
        exposure_for_computation: ExposureForComputation,
    ) -> tuple[
        bool,
        SingleBrightPointInFrame | None,
        ProjectionAlignmentLedNumber | None
    ]:

        base_led = projection_alignment_led_number.value
        exposure = exposure_for_computation.value

        # ★ LED 総数を取得
        led_count = self.led_control_service.led_driver.get_led_count()

        # ★ 探索順序（0, +1, -1, +2, -2, ...）
        search_order = []
        for offset in range(led_count):
            if offset == 0:
                search_order.append(base_led)
            else:
                search_order.append((base_led + offset) % led_count)
                search_order.append((base_led - offset) % led_count)

            if len(search_order) >= led_count:
                break

        # ---------------------------------------------------------
        # ★ 探索ループ
        # ---------------------------------------------------------
        for led_to_try in search_order:

            # --- LED 点灯 ---
            self.led_control_service.turn_only(led_to_try)
            self._logger.debug(f"SingleLedPositionDetectionService: LED {led_to_try} を点灯")

            # --- 撮像 ---
            frame = self.camera_capture_service.capture_with_exposure(exposure)

            # --- LED 消灯 ---
            self.led_control_service.turn_off_all()

            if frame is None:
                self._logger.error("SingleLedPositionDetectionService: 撮像に失敗しました")
                continue

            # --- 輝点検出 ---
            detected_points = self.red_light_detection_service.detect(frame)
            count = len(detected_points.coords_in_frame)

            # --- 1点だけ検出されたら成功 ---
            if count == 1:
                coord = detected_points.coords_in_frame.astype(np.int32).reshape(1, 2)
                point = SingleBrightPointInFrame.create(coord)

                if point is False:
                    self._logger.error("SingleBrightPointInFrame の生成に失敗")
                    return False, None, None

                # ★ 検出された LED 番号を VO として返す
                detected_led_vo = ProjectionAlignmentLedNumber.create(led_to_try)

                x, y = point.coord_in_frame[0]
                self._logger.debug(
                    f"SingleLedPositionDetectionService: LED {led_to_try} の位置を検出: ({x}, {y})"
                )

                return True, point, detected_led_vo

            # --- 複数検出はエラー扱い ---
            if count > 1:
                self._logger.error(
                    f"SingleLedPositionDetectionService: LED {led_to_try} の輝点が複数検出されました（{count} 個）"
                )
                continue

            # --- 0個 → 次の LED を試す ---
            self._logger.debug(
                f"SingleLedPositionDetectionService: LED {led_to_try} では輝点が検出されませんでした → 次へ"
            )

        # ---------------------------------------------------------
        # ★ 全 LED を探索しても見つからなかった
        # ---------------------------------------------------------
        self._logger.error(
            "SingleLedPositionDetectionService: 全 LED を探索しましたが輝点が検出されませんでした"
        )

        # ★ 安全のため全 LED OFF
        self.led_control_service.turn_off_all()

        # ★ 30 秒待機
        self._logger.error("SingleLedPositionDetectionService: 30 秒待機します")
        import time
        time.sleep(20)

        return False, None, None
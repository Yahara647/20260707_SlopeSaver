# src/application/usecases/full_reflection_measurement_usecase.py

from __future__ import annotations

import numpy as np
from logger.logger import logger

# --- Interfaces ---
from domain.interfaces.i_camera_service import ICameraService
from domain.interfaces.i_led_driver import ILedDriver

# --- Services ---
from application.services.measurement.single_led_position_detection_service import SingleLedPositionDetectionService
from application.services.measurement.compute_low_exposure_service import ComputeLowExposureService

# --- ValueObjects ---
from domain.value_objects.config_values.projection_alignment_led_number import ProjectionAlignmentLedNumber
from domain.value_objects.config_values.exposure_for_computation import ExposureForComputation
from domain.value_objects.config_values.led_coordinates import LedCoordinates
from domain.value_objects.config_values.camera_coordinate import CameraCoordinate
from domain.value_objects.computed_values.homography_matrix import HomographyMatrix
from domain.value_objects.config_values.strip_z import StripZ

from domain.value_objects.computed_values.single_bright_point_in_frame import SingleBrightPointInFrame
from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame
from domain.value_objects.computed_values.red_bright_points_in_world import RedBrightPointsInWorld
from domain.value_objects.computed_values.led_numbers_in_frame import LedNumbersInFrame
from domain.value_objects.computed_values.strip_slopes import StripSlopes
from domain.value_objects.computed_values.slope_angles import SlopeAngles



class FullReflectionMeasurementUseCase:
    """
    LED1点位置検出 → 全LED点灯で勾配計算 をまとめて実行する UseCase。

    - 依存は ICameraService / ILedDriver のみ
    - 内部で 2 つのサービスを組み立てる
    """

    def __init__(
        self,
        camera_service: ICameraService,
        led_driver: ILedDriver,
    ) -> None:

        self._logger = logger

        # --- 内部サービス構築 ---
        self.single_led_detection_service = SingleLedPositionDetectionService(
            camera_service=camera_service,
            led_driver=led_driver,
        )

        self.compute_low_exposure_service = ComputeLowExposureService(
            camera_service=camera_service,
            led_driver=led_driver,
        )

    # ---------------------------------------------------------
    # メイン処理
    # ---------------------------------------------------------
    def run(
        self,
        projection_alignment_led_number: ProjectionAlignmentLedNumber,
        exposure_for_computation: ExposureForComputation,
        led_coordinates: LedCoordinates,
        camera_coordinate: CameraCoordinate,
        homography_matrix: HomographyMatrix,
        strip_z: StripZ,
    ) -> tuple[
        bool,
        SingleBrightPointInFrame | None,
        LedNumbersInFrame | None,
        RedBrightPointsInFrame | None,
        RedBrightPointsInWorld | None,
        LedCoordinates | None,
        StripSlopes | None,
        SlopeAngles | None
    ]:

        # ---------------------------------------------------------
        # ① LED1点位置検出（返り値は 3 つ）
        # ---------------------------------------------------------
        success, marker_led_coord_in_frame, detected_led_number = \
            self.single_led_detection_service.run(
                projection_alignment_led_number=projection_alignment_led_number,
                exposure_for_computation=exposure_for_computation,
            )

        if not success:
            self._logger.error("FullReflectionMeasurementUseCase: marker LED の位置検出に失敗")
            return False, None, None, None, None, None, None, None

        # ---------------------------------------------------------
        # ★ AppConfig に検出された LED 番号を反映
        # ---------------------------------------------------------
        try:
            self._logger.info(
                f"FullReflectionMeasurementUseCase: 検出された LED 番号 {detected_led_number.value} を AppConfig に反映"
            )
            # ProjectionAlignmentLedNumber は VO なので value を更新
            projection_alignment_led_number.value = detected_led_number.value

        except Exception as e:
            self._logger.error(f"AppConfig への LED 番号反映に失敗: {e}")

        # ---------------------------------------------------------
        # ② 全LED点灯 → 勾配計算
        # ---------------------------------------------------------
        (
            success,
            led_numbers_in_frame,
            red_bright_points_in_frame,
            red_bright_points_in_world,
            led_world_coords_in_frame,
            reflection_normals,
            strip_slopes,
            slope_angles,
        ) = self.compute_low_exposure_service.run(
            exposure_for_computation=exposure_for_computation,
            projection_alignment_led_number=detected_led_number,
            marker_led_coord_in_frame=marker_led_coord_in_frame,
            led_coordinates=led_coordinates,
            camera_coordinate=camera_coordinate,
            homography_matrix=homography_matrix,
            strip_z=strip_z,
        )

        if not success:
            self._logger.error("FullReflectionMeasurementUseCase: 勾配計算に失敗")
            return False, marker_led_coord_in_frame, None, None, None, None, None, None

        # ---------------------------------------------------------
        # ★ ③ 勾配計算後：LED 番号を中央値に更新
        # ---------------------------------------------------------
        if led_numbers_in_frame is not None and not led_numbers_in_frame.is_empty:

            # 中央値を取得
            median_led = int(np.median(led_numbers_in_frame.led_nums))

            # 新しい VO を作成
            new_led_vo = ProjectionAlignmentLedNumber.create(median_led)

            if new_led_vo is False:
                self._logger.error(
                    f"FullReflectionMeasurementUseCase: 中央値 LED {median_led} の VO 生成に失敗"
                )
            else:
                # AppConfig の値を更新（再代入）
                self._logger.info(
                    f"FullReflectionMeasurementUseCase: LED 番号を中央値 {median_led} に更新"
                )
                projection_alignment_led_number.value = new_led_vo.value
        else:
            self._logger.error(
                "FullReflectionMeasurementUseCase: led_numbers_in_frame が空のため中央値を更新できません"
            )

        # ---------------------------------------------------------
        # ③ 正常終了（返り値に LED 番号は含めない）
        # ---------------------------------------------------------
        return (
            True,
            marker_led_coord_in_frame,
            led_numbers_in_frame,
            red_bright_points_in_frame,
            red_bright_points_in_world,
            led_world_coords_in_frame,
            reflection_normals,
            strip_slopes,
            slope_angles,
        )

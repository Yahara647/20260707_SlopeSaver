# src/application/services/measurement/compute_low_exposure_service.py

from __future__ import annotations

from logger.logger import logger
import time

# --- Interfaces ---
from domain.interfaces.i_camera_service import ICameraService
from domain.interfaces.i_led_driver import ILedDriver

# --- Application Services ---
from application.services.led.led_control_service import LedControlService
from application.services.camera.camera_control_service import CameraControlService
from application.services.camera.camera_capture_service import CameraCaptureService
from application.services.image_processing.red_light_detection_service import RedLightDetectionService

# --- Domain Services ---
from domain.services.single_led_alignment_service import SingleLedAlignmentService
from domain.services.led_world_coordinate_resolver_service import LedWorldCoordinateResolverService
from domain.services.reflection_normal_calculator_service import ReflectionNormalCalculatorService
from domain.services.slope_calculator_service import SlopeCalculatorService
from domain.services.red_light_detector import RedLightDetector
from domain.services.homography_transformer import HomographyTransformer

# --- ValueObjects ---
from domain.value_objects.config_values.exposure_for_computation import ExposureForComputation
from domain.value_objects.config_values.projection_alignment_led_number import ProjectionAlignmentLedNumber
from domain.value_objects.computed_values.single_bright_point_in_frame import SingleBrightPointInFrame
from domain.value_objects.config_values.led_coordinates import LedCoordinates
from domain.value_objects.config_values.camera_coordinate import CameraCoordinate
from domain.value_objects.computed_values.homography_matrix import HomographyMatrix
from domain.value_objects.config_values.strip_z import StripZ

from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame
from domain.value_objects.computed_values.red_bright_points_in_world import RedBrightPointsInWorld
from domain.value_objects.computed_values.led_numbers_in_frame import LedNumbersInFrame
from domain.value_objects.computed_values.led_world_coordinates_in_frame import LedWorldCoordinatesInFrame
from domain.value_objects.computed_values.normal_vectors import NormalVectors
from domain.value_objects.computed_values.strip_slopes import StripSlopes
from domain.value_objects.computed_values.slope_angles import SlopeAngles


class ComputeLowExposureService:

    def __init__(
        self,
        camera_service: ICameraService,
        led_driver: ILedDriver,
    ) -> None:

        self._logger = logger

        # --- Application Services ---
        self.led_control_service = LedControlService(led_driver=led_driver, logger=logger)
        self.camera_control_service = CameraControlService(driver=camera_service, state=camera_service.state, logger=logger)
        self.camera_capture_service = CameraCaptureService(camera_service=camera_service, camera_state=camera_service.state, logger=logger)

        detector = RedLightDetector()
        self.red_light_detection_service = RedLightDetectionService(detector)

        # --- Domain Services ---
        self.alignment_service = SingleLedAlignmentService(logger=logger)
        self.homography_transformer = HomographyTransformer()
        self.world_resolver_service = LedWorldCoordinateResolverService(logger=logger)
        self.normal_calc_service = ReflectionNormalCalculatorService(logger=logger)
        self.slope_calc_service = SlopeCalculatorService(logger=logger)

    def run(
        self,
        exposure_for_computation: ExposureForComputation,
        projection_alignment_led_number: ProjectionAlignmentLedNumber,
        marker_led_coord_in_frame: SingleBrightPointInFrame,
        led_coordinates: LedCoordinates,
        camera_coordinate: CameraCoordinate,
        homography_matrix: HomographyMatrix,
        strip_z: StripZ,
    ) -> tuple[
        bool,
        LedNumbersInFrame | None,
        RedBrightPointsInFrame | None,
        RedBrightPointsInWorld | None,
        LedWorldCoordinatesInFrame | None,
        NormalVectors | None,
        StripSlopes | None,
        SlopeAngles | None
    ]:

        # ① LED 全点灯
        self.led_control_service.turn_on_all()
        # time.sleep(0.1)

        # ②〜③：露光変更＋撮像
        frame = self.camera_capture_service.capture_with_exposure(exposure_for_computation.value)
        if frame is None:
            self._logger.error("ComputeLowExposureService: 撮像に失敗")
            return False, None, None, None, None, None, None
        self.led_control_service.turn_off_all()

        # ④ 赤色輝点検出
        red_bright_points_in_frame = self.red_light_detection_service.detect(frame)
        if red_bright_points_in_frame.is_empty:
            self._logger.warning("ComputeLowExposureService: 赤色輝点が検出されませんでした")
            return False, None, None, None, None, None, None

        # ⑤ LED 番号割当
        success, led_numbers_in_frame, aligned_red_bright_points_in_frame = \
            self.alignment_service.assign(
                marker_led_num=projection_alignment_led_number,
                marker_led_coord=marker_led_coord_in_frame,
                detected_coords=red_bright_points_in_frame,
            )

        if not success:
            self._logger.warning("ComputeLowExposureService: LED 番号割当に失敗")
            return False, None, None, None, None, None, None

        # ⑥ 赤輝点の世界座標変換（ホモグラフィ＋Z）
        red_bright_points_in_world = self.homography_transformer.transform_points(
            H=homography_matrix,
            points_in_frame=aligned_red_bright_points_in_frame,
            strip_z=strip_z.value,
        )

        # ⑦ LED 世界座標（LED番号に基づいて並び替え）
        success_world, led_world_coords_in_frame = self.world_resolver_service.resolve(
            led_nums=led_numbers_in_frame,
            led_coordinates=led_coordinates,
        )

        if not success_world:
            self._logger.error("ComputeLowExposureService: LED 世界座標の解決に失敗")
            return False, None, None, None, None, None, None

        # ⑧ 法線計算
        success_normals, reflection_normals = self.normal_calc_service.calculate(
            led_world_coords=led_world_coords_in_frame,
            red_world_coords=red_bright_points_in_world,
            camera_coord=camera_coordinate,
        )

        if not success_normals:
            self._logger.error("ComputeLowExposureService: 法線計算に失敗")
            return False, None, None, None, None, None, None

        # ⑨ 勾配計算
        success, strip_slopes, slope_angles = self.slope_calc_service.calculate(reflection_normals)

        return (
            True,
            led_numbers_in_frame,
            aligned_red_bright_points_in_frame,
            red_bright_points_in_world,
            led_world_coords_in_frame,
            reflection_normals,
            strip_slopes,
            slope_angles,
        )

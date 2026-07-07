from __future__ import annotations
from typing import Tuple
from logging import Logger
import numpy as np

# --- Domain Services ---
from domain.services.single_led_alignment_service import SingleLedAlignmentService
from domain.services.led_world_coordinate_resolver_service import LedWorldCoordinateResolverService
from domain.services.reflection_normal_calculator_service import ReflectionNormalCalculatorService
from domain.services.slope_calculator_service import SlopeCalculatorService

# --- Domain ValueObjects ---
from domain.value_objects.computed_values.single_bright_point_in_frame import SingleBrightPointInFrame
from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame
from domain.value_objects.computed_values.red_bright_points_in_world import RedBrightPointsInWorld
from domain.value_objects.config_values.led_coordinates import LedCoordinates
from domain.value_objects.config_values.camera_coordinate import CameraCoordinate
from domain.value_objects.computed_values.led_numbers_in_frame import LedNumbersInFrame
from domain.value_objects.computed_values.led_world_coordinates_in_frame import LedWorldCoordinatesInFrame
from domain.value_objects.computed_values.normal_vectors import NormalVectors
from domain.value_objects.computed_values.slope_angles import SlopeAngles
from domain.value_objects.computed_values.homography_matrix import HomographyMatrix

# --- Infra Services ---
from application.services.led.led_control_service import LedControlService
from application.services.camera.camera_control_service import CameraControlService
from application.services.camera.camera_capture_service import CameraCaptureService
from application.services.image_processing.red_light_detection_service import RedLightDetectionService

# --- Homography ---
from domain.services.homography_transformer import HomographyTransformer


class FullReflectionMeasurementService:
    """
    LED → 輝点 → LED 番号 → 世界座標 → 法線 → 勾配
    の一連の処理をまとめて実行する Application Service。
    """

    def __init__(
        self,
        led_control: LedControlService,
        camera_control: CameraControlService,
        camera_capture: CameraCaptureService,
        red_light_detector: RedLightDetectionService,
        alignment_service: SingleLedAlignmentService,
        world_resolver_service: LedWorldCoordinateResolverService,
        normal_calc_service: ReflectionNormalCalculatorService,
        slope_calc_service: SlopeCalculatorService,
        logger: Logger | None = None
    ) -> None:

        self.led_control = led_control
        self.camera_control = camera_control
        self.camera_capture = camera_capture
        self.red_light_detector = red_light_detector

        self.alignment_service = alignment_service
        self.world_resolver_service = world_resolver_service
        self.normal_calc_service = normal_calc_service
        self.slope_calc_service = slope_calc_service

        self.logger = logger

    # ---------------------------------------------------------
    # メイン処理
    # ---------------------------------------------------------
    def execute(
        self,
        marker_led_num: int,
        marker_led_coord: SingleBrightPointInFrame,
        exposure_us: float,
        led_coordinates: LedCoordinates,
        camera_coord: CameraCoordinate,
        homography_matrix: HomographyMatrix,   # ★ ndarray → HomographyMatrix に変更
        strip_z: float
    ) -> Tuple[
        bool,
        LedNumbersInFrame | None,
        RedBrightPointsInFrame | None,
        RedBrightPointsInWorld | None,
        LedWorldCoordinatesInFrame | None,
        NormalVectors | None,
        SlopeAngles | None
    ]:

        # --- 現在の露光を保存 ---
        original_exposure = self.camera_control.get_exposure()

        # --- LED 全点灯 ---
        self.led_control.turn_on_all()

        # --- 露光変更 ---
        self.camera_control.set_exposure(exposure_us)

        # --- 撮像 ---
        frame = self.camera_capture.capture_once()

        # --- LED 消灯 & 露光復帰 ---
        self.led_control.turn_off_all()
        self.camera_control.set_exposure(original_exposure)

        if frame is None:
            return False, None, None, None, None, None, None

        # --- 輝点検出 ---
        detected_points: RedBrightPointsInFrame = self.red_light_detector.detect(frame)

        # --- LED 番号割り当て ---
        success, led_nums, aligned_pixel_coords = self.alignment_service.assign(
            marker_led_num=marker_led_num,
            marker_led_coord=marker_led_coord,
            detected_coords=detected_points
        )
        if not success:
            return False, None, None, None, None, None, None

        # --- LED 世界座標を導出 ---
        success, led_world_coords = self.world_resolver_service.resolve(
            led_nums=led_nums,
            led_coordinates=led_coordinates
        )
        if not success:
            return False, led_nums, aligned_pixel_coords, None, None, None, None

        # ---------------------------------------------------------
        # ★ Homography による反射点の世界座標変換（ValueObject をそのまま渡す）
        # ---------------------------------------------------------
        transformer = HomographyTransformer()

        red_world: RedBrightPointsInWorld = transformer.transform_points(
            H=homography_matrix,                 # ★ create() を呼ばず、そのまま渡す
            points_in_frame=aligned_pixel_coords,
            strip_z=strip_z
        )

        if red_world is False:
            return False, led_nums, aligned_pixel_coords, None, None, None, None

        # --- 法線ベクトル計算 ---
        success, normals = self.normal_calc_service.calculate(
            led_world_coords=led_world_coords,
            red_world_coords=red_world,
            camera_coord=camera_coord
        )
        if not success:
            return False, led_nums, aligned_pixel_coords, red_world, led_world_coords, None, None

        # --- 勾配計算 ---
        success, slopes = self.slope_calc_service.calculate(normals)
        if not success:
            return False, led_nums, aligned_pixel_coords, red_world, led_world_coords, normals, None

        return True, led_nums, aligned_pixel_coords, red_world, led_world_coords, normals, slopes

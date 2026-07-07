from dataclasses import dataclass

from domain.value_objects.config_values.led_reflection_area import LedReflectionArea
from domain.value_objects.config_values.camera_coordinate import CameraCoordinate
from domain.value_objects.config_values.led_coordinates import LedCoordinates
from domain.value_objects.config_values.window_size import WindowSize
from domain.value_objects.config_values.strip_z import StripZ
from domain.value_objects.config_values.calibration_leds_in_world import CalibrationLedsInWorld

from domain.value_objects.config_values.projection_alignment_led_number import ProjectionAlignmentLedNumber
from domain.value_objects.config_values.exposure_for_computation import ExposureForComputation
from domain.value_objects.config_values.exposure_for_display import ExposureForDisplay

# ← 新規追加
from domain.value_objects.config_values.app_flags import AppFlags


@dataclass
class AppConfig:
    """
    アプリ全体の設定を保持するアグリゲートルート。

    - led_reflection_area            : LED 反射領域（ROI）
    - camera_coordinate              : カメラの世界座標
    - led_coordinates                : 複数 LED の世界座標
    - calibration_leds_in_world      : キャリブレーション用 LED の世界座標
    - window_size                    : GUI ウィンドウサイズ
    - strip_z                        : 帯鋼の Z 座標（計測平面の高さ）

    - projection_alignment_led_number: 投影LEDの位置合わせに使用する LED 番号
    - exposure_for_computation       : 計算用画像の露光時間
    - exposure_for_display           : 表示用画像の露光時間

    - app_flags                      : アプリ動作フラグ（終了・停止・表示ON/OFF）

    ※ AppConfig 自体は永続化ロジックを持たず、
       JSON 読み書きは Application 層の Mapper が担当する。
    """

    led_reflection_area: LedReflectionArea
    camera_coordinate: CameraCoordinate
    led_coordinates: LedCoordinates
    calibration_leds_in_world: CalibrationLedsInWorld
    window_size: WindowSize
    strip_z: StripZ

    projection_alignment_led_number: ProjectionAlignmentLedNumber
    exposure_for_computation: ExposureForComputation
    exposure_for_display: ExposureForDisplay

    app_flags: AppFlags

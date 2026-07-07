from dataclasses import dataclass

from domain.value_objects.computed_values.slope_angles import SlopeAngles
from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame
from domain.value_objects.computed_values.red_bright_points_in_world import RedBrightPointsInWorld
from domain.value_objects.computed_values.led_numbers_in_frame import LedNumbersInFrame
from domain.value_objects.computed_values.led_world_coordinates_in_frame import LedWorldCoordinatesInFrame
from domain.value_objects.computed_values.normal_vectors import NormalVectors
from domain.value_objects.computed_values.strip_slopes import StripSlopes


@dataclass(frozen=True)
class SlopeComputationResult:
    """
    勾配計算フェーズで得られるすべての計算結果を集約するアグリゲートルート。

    - slope_angles                 : 法線ベクトルから算出された X/Y 勾配角度
    - red_bright_points_in_frame  : 画像内で検出された赤色点の画素座標
    - red_bright_points_in_world  : 赤色点の世界座標
    - led_numbers_in_frame        : 勾配計算対象となった LED 番号の集合
    - led_world_coordinates_in_frame : LED 番号に対応する世界座標
    - normal_vectors              : 各点における法線ベクトル
    - strip_slopes                : 1フレーム分の傾斜角 (slope_x, slope_y)
    """

    slope_angles: SlopeAngles
    red_bright_points_in_frame: RedBrightPointsInFrame
    red_bright_points_in_world: RedBrightPointsInWorld
    led_numbers_in_frame: LedNumbersInFrame
    led_world_coordinates_in_frame: LedWorldCoordinatesInFrame
    normal_vectors: NormalVectors
    strip_slopes: StripSlopes

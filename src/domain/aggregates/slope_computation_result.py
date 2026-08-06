from dataclasses import dataclass

from domain.value_objects.computed_values.slope_angles import SlopeAngles
from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame
from domain.value_objects.computed_values.led_numbers_in_frame import LedNumbersInFrame
from domain.value_objects.computed_values.slit_light_points_in_frame import SlitLightPointsInFrame
from domain.value_objects.computed_values.slit_light_source_z_coords import SlitLightSourceZCoords
from domain.value_objects.computed_values.slit_light_points_in_world import SlitLightPointsInWorld
from domain.value_objects.computed_values.normal_vectors import NormalVectors


@dataclass(frozen=True)
class SlopeComputationResult:
    """
    スリット光計測パイプラインの全計算結果を集約するアグリゲートルート。

    フェーA（LED位置検出）:
    - led_points_in_frame          : LED投影点の画像座標
    - led_numbers_in_frame         : 各LEDのハードウェア番号

    フェーB（スリット光検出～勾配計算）:
    - slit_points_in_frame         : スリット光点の画像座標 (x, y)
    - slit_source_z_coords         : スリット光源のz座標（LED y-zマッピングから）
    - slit_points_in_world         : スリット光反射点の実空間座標
    - normal_vectors               : 各点の法線ベクトル
    - slope_angles                 : X/Y方向の勾配角度
    """

    # フェーA
    led_points_in_frame: RedBrightPointsInFrame
    led_numbers_in_frame: LedNumbersInFrame

    # フェーB
    slit_points_in_frame: SlitLightPointsInFrame
    slit_source_z_coords: SlitLightSourceZCoords
    slit_points_in_world: SlitLightPointsInWorld
    normal_vectors: NormalVectors
    slope_angles: SlopeAngles

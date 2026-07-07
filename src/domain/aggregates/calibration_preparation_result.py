from dataclasses import dataclass
from domain.value_objects.computed_values.calibration_leds_in_frame import CalibrationLedsInFrame
from domain.value_objects.computed_values.homography_matrix import HomographyMatrix

@dataclass
class CalibrationPreparationResult:
    """
    勾配計算の前準備（校正フェーズ）で得られる計算結果を
    ひとまとめに保持するアグリゲートルート。

    - calibration_leds_in_frame : 画像内で選択されたキャリブレーション LED の画素座標
    - homography_matrix         : 画素座標 → 世界座標変換のためのホモグラフィ行列

    ※ 計算結果であり、永続化は Application 層の Mapper が担当する。
    """

    calibration_leds_in_frame: CalibrationLedsInFrame
    homography_matrix: HomographyMatrix

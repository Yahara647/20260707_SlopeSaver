from dataclasses import dataclass
from domain.value_objects.computed_values.single_bright_point_in_frame import SingleBrightPointInFrame

@dataclass(frozen=True)
class ProjectionAlignmentResult:
    """
    勾配計算の前準備（投影LEDの位置合わせフェーズ）で得られる
    計算結果をひとまとめに保持するアグリゲートルート。

    - single_bright_point_in_frame : 投影LEDとして検出された単一点の画素座標

    ※ 今後、位置合わせ誤差や補正後座標などの ValueObject を
       追加する場合はフィールドを増やして拡張する。
    """

    single_bright_point_in_frame: SingleBrightPointInFrame

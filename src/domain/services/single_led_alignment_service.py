from __future__ import annotations
from typing import Tuple
import numpy as np
from logging import Logger

from domain.value_objects.config_values.projection_alignment_led_number import ProjectionAlignmentLedNumber
from domain.value_objects.computed_values.single_bright_point_in_frame import SingleBrightPointInFrame
from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame
from domain.value_objects.computed_values.led_numbers_in_frame import LedNumbersInFrame


class SingleLedAlignmentService:
    """
    基準 LED（marker_led_num）に最も近い検出点を基準点として採用し、
    そこから上下に LED 番号を割り当てるサービス。
    """

    def __init__(self, logger: Logger | None = None) -> None:
        self.logger = logger

    def assign(
        self,
        marker_led_num: ProjectionAlignmentLedNumber,
        marker_led_coord: SingleBrightPointInFrame,
        detected_coords: RedBrightPointsInFrame
    ) -> Tuple[bool, LedNumbersInFrame | None, RedBrightPointsInFrame | None]:

        # --- 入力チェック ---
        if detected_coords.is_empty:
            if self.logger:
                self.logger.error("SingleLedAlignmentService: detected_coords が空です")
            return False, None, None

        detected = detected_coords.coords_in_frame
        marker = marker_led_coord.coord_in_frame

        # --- y 座標でソート ---
        try:
            sorted_coords = detected[np.argsort(detected[:, 1])]
        except Exception as e:
            if self.logger:
                self.logger.error(f"SingleLedAlignmentService: ソート中にエラー: {e}")
            return False, None, None

        # --- 基準 LED に最も近い点を探す ---
        try:
            dists = np.linalg.norm(sorted_coords - marker[0], axis=1)
            marker_index = np.argmin(dists)
        except Exception as e:
            if self.logger:
                self.logger.error(f"SingleLedAlignmentService: 距離計算に失敗: {e}")
            return False, None, None

        base = marker_led_num.value  # ★ VO → int

        result = []

        # --- 基準点より上（y が小さい） → LED 番号を増やす ---
        for i in range(marker_index - 1, -1, -1):
            led_num = base - (marker_index - i)
            result.append((led_num, tuple(sorted_coords[i])))

        # --- 基準点自身 ---
        result.append((base, tuple(sorted_coords[marker_index])))

        # --- 基準点より下（y が大きい） → LED 番号を減らす ---
        for i in range(marker_index + 1, len(sorted_coords)):
            led_num = base + (i - marker_index)
            result.append((led_num, tuple(sorted_coords[i])))

        # --- LED 番号順に並べ替え ---
        result.sort(key=lambda x: x[0])

        # --- LED 番号配列を作成 ---
        led_nums_np = np.array([item[0] for item in result], dtype=np.int32)
        led_nums_vo = LedNumbersInFrame.create(led_nums_np)
        if led_nums_vo is False:
            if self.logger:
                self.logger.error("SingleLedAlignmentService: LedNumbersInFrame の生成に失敗")
            return False, None, None

        # --- 画素座標配列を作成 ---
        pixel_coords_np = np.array([item[1] for item in result], dtype=np.int32)
        pixel_coords_vo = RedBrightPointsInFrame.create(pixel_coords_np)
        if pixel_coords_vo is False:
            if self.logger:
                self.logger.error("SingleLedAlignmentService: RedBrightPointsInFrame の生成に失敗")
            return False, None, None

        if self.logger:
            self.logger.debug(f"SingleLedAlignmentService: 割り当て完了 led_nums={led_nums_np}")

        return True, led_nums_vo, pixel_coords_vo

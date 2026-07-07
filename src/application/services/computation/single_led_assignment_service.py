# src/domain/services/single_led_assignment_service.py

from __future__ import annotations
from typing import Tuple
import numpy as np
from logging import Logger

from domain.value_objects.computed_values.single_bright_point_in_frame import SingleBrightPointInFrame


class SingleLedAssignmentService:
    """
    1つの LED 番号に対して、
    ・その LED の理想的な画素座標（target_coord）
    ・複数の検出点（detected_coords）
    の中から最も近い点を割り当てるサービス。

    ※世界座標は扱わない。
    """

    def __init__(self, logger: Logger | None = None) -> None:
        self.logger = logger

    def assign(
        self,
        led_num: int,
        target_coord: np.ndarray,          # shape=(1,2)
        detected_coords: np.ndarray        # shape=(N,2)
    ) -> Tuple[bool, SingleBrightPointInFrame | None]:
        """
        Parameters
        ----------
        led_num : int
            割り当てたい LED 番号
        target_coord : np.ndarray
            その LED の理想的な画素座標（shape=(1,2), int32）
        detected_coords : np.ndarray
            検出された複数の輝点座標（shape=(N,2), int32）

        Returns
        -------
        (success, point)
            success : bool
            point   : SingleBrightPointInFrame | None
        """

        # --- 入力チェック ---
        if detected_coords is None or len(detected_coords) == 0:
            if self.logger:
                self.logger.error(
                    f"SingleLedAssignmentService: LED {led_num} に割り当て可能な点がありません"
                )
            return False, None

        if target_coord.shape != (1, 2):
            if self.logger:
                self.logger.error(
                    f"SingleLedAssignmentService: target_coord の shape が不正: {target_coord.shape}"
                )
            return False, None

        # --- 距離計算 ---
        try:
            dists = np.linalg.norm(detected_coords - target_coord[0], axis=1)
            idx = np.argmin(dists)
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"SingleLedAssignmentService: 距離計算に失敗: {e}"
                )
            return False, None

        # --- 最も近い点を取得 ---
        nearest = detected_coords[idx].astype(np.int32).reshape(1, 2)

        point = SingleBrightPointInFrame.create(nearest)
        if point is False:
            if self.logger:
                self.logger.error(
                    f"SingleLedAssignmentService: SingleBrightPointInFrame の生成に失敗"
                )
            return False, None

        if self.logger:
            x, y = point.coord_in_frame[0]
            self.logger.debug(
                f"SingleLedAssignmentService: LED {led_num} に ({x}, {y}) を割り当て"
            )

        return True, point

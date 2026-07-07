from __future__ import annotations
from typing import Tuple
import numpy as np
from logging import Logger

from domain.value_objects.computed_values.normal_vectors import NormalVectors
from domain.value_objects.computed_values.strip_slopes import StripSlopes
from domain.value_objects.computed_values.slope_angles import SlopeAngles


class SlopeCalculatorService:
    """
    NormalVectors（法線ベクトル群）から
    X・Y 方向の勾配角度（度数法）を算出する Domain Service。

    以前の SlopeCalculator と同じ計算式を使用する。
    """

    def __init__(self, logger: Logger | None = None) -> None:
        self.logger = logger

    def calculate(
        self,
        normals: NormalVectors
    ) -> Tuple[bool, SlopeAngles | None]:
        """
        Parameters
        ----------
        normals : NormalVectors
            法線ベクトル群（shape=(N,3)）

        Returns
        -------
        (success, slope_angles)
            success : bool
            slope_angles : SlopeAngles
        """

        if normals.normals_in_world is None or len(normals.normals_in_world) == 0:
            if self.logger:
                self.logger.error("SlopeCalculatorService: normals が空です")
            return False, None

        normals_np = normals.normals_in_world
        slopes = []
        slopes_deg = []

        for n in normals_np:
            # --- 入力チェック ---
            if n.shape != (3,) or np.isnan(n).any():
                slopes.append([np.nan, np.nan])
                slopes_deg.append([np.nan, np.nan])
                continue

            nx, ny, nz = n

            if nz == 0:
                slopes.append([np.nan, np.nan])
                slopes_deg.append([np.nan, np.nan])
                continue

            # --- 以前の計算式と完全一致 ---

            x_slope = - nx / nz
            y_slope = - ny / nz

            slopes.append([x_slope, y_slope])

            x_slope_deg = -np.degrees(np.arctan2(nx, nz))
            y_slope_deg = -np.degrees(np.arctan2(ny, nz))

            slopes_deg.append([x_slope_deg, y_slope_deg])
        
        slopes_np = np.array(slopes, dtype=float)
        slopes_np_deg = np.array(slopes_deg, dtype=float)

        slopes_vo = StripSlopes.create(slopes_np)
        slopes_vo_deg = SlopeAngles.create(slopes_np_deg)

        if slopes_vo_deg is False:
            if self.logger:
                self.logger.error("SlopeCalculatorService: SlopeAngles の生成に失敗")
            return False, None

        if self.logger:
            self.logger.debug("SlopeCalculatorService: 勾配角度計算完了")

        return True, slopes_vo, slopes_vo_deg

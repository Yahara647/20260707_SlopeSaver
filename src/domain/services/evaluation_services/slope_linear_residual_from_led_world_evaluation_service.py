from __future__ import annotations
import numpy as np

from domain.value_objects.computed_values.slope_angles import SlopeAngles
from domain.value_objects.computed_values.led_world_coordinates_in_frame import LedWorldCoordinatesInFrame

from domain.value_objects.evaluation_values.slope_linear_residuals import SlopeLinearResiduals
from domain.value_objects.evaluation_values.slope_mean_residuals import SlopeMeanResiduals
from domain.value_objects.evaluation_values.slope_quadratic_residuals import SlopeQuadraticResiduals


class SlopeLinearResidualFromLedWorldEvaluationService:
    """
    SlopeAngles と LedWorldCoordinatesInFrame を用いて、
    slope_x / slope_y を world-y に対して評価するサービス。

    - 一次近似残差（SlopeLinearResiduals）
    - 平均値残差（SlopeMeanResiduals）
    - 二次近似残差（SlopeQuadraticResiduals）
    を別々の ValueObject として返す。
    """

    @staticmethod
    def evaluate(
        slope_angles: SlopeAngles,
        led_world_coords: LedWorldCoordinatesInFrame,
    ) -> tuple[
        SlopeLinearResiduals,
        SlopeMeanResiduals,
        SlopeQuadraticResiduals
    ]:

        if slope_angles.is_empty or led_world_coords.is_empty:
            raise ValueError("Input data is empty.")

        slopes = slope_angles.slopes_in_world
        coords = led_world_coords.coords_in_world  # shape=(N,3)

        if slopes.shape[0] != coords.shape[0]:
            raise ValueError("SlopeAngles と LedWorldCoordinatesInFrame の点数が一致しません。")

        # world-z を横軸にする
        xs = coords[:, 2]

        ys_x = slopes[:, 0]
        ys_y = slopes[:, 1]

        # -----------------------------
        # ① 一次近似残差
        # -----------------------------
        coef_x_1 = np.polyfit(xs, ys_x, 1)
        coef_y_1 = np.polyfit(xs, ys_y, 1)

        pred_x_1 = np.polyval(coef_x_1, xs)
        pred_y_1 = np.polyval(coef_y_1, xs)

        linear_residuals = np.column_stack([ys_x - pred_x_1, ys_y - pred_y_1])
        linear_vo = SlopeLinearResiduals.create(linear_residuals)

        # -----------------------------
        # ② 平均値残差
        # -----------------------------
        mean_x = np.mean(ys_x)
        mean_y = np.mean(ys_y)

        mean_residuals = np.column_stack([ys_x - mean_x, ys_y - mean_y])
        mean_vo = SlopeMeanResiduals.create(mean_residuals)

        # -----------------------------
        # ③ 二次近似残差
        # -----------------------------
        coef_x_2 = np.polyfit(xs, ys_x, 2)
        coef_y_2 = np.polyfit(xs, ys_y, 2)

        pred_x_2 = np.polyval(coef_x_2, xs)
        pred_y_2 = np.polyval(coef_y_2, xs)

        quad_residuals = np.column_stack([ys_x - pred_x_2, ys_y - pred_y_2])
        quad_vo = SlopeQuadraticResiduals.create(quad_residuals)

        return linear_vo, mean_vo, quad_vo

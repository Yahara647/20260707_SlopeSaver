from __future__ import annotations

import numpy as np

from domain.aggregates.measurement_evaluation_result import MeasurementEvaluationResult
from domain.aggregates.slope_computation_result import SlopeComputationResult
from domain.value_objects.evaluation_values.slope_distortion_evaluation import (
    SlopeDistortionEvaluation,
)
from domain.value_objects.evaluation_values.slope_linear_residuals import (
    SlopeLinearResiduals,
)
from domain.value_objects.evaluation_values.slope_linear_residuals_max_adjusted import (
    SlopeLinearResidualsMaxAdjusted,
)
from domain.value_objects.evaluation_values.slope_linear_residuals_min_adjusted import (
    SlopeLinearResidualsMinAdjusted,
)
from domain.value_objects.evaluation_values.slope_mean_residuals import SlopeMeanResiduals
from domain.value_objects.evaluation_values.slope_mean_residuals_max_adjusted import (
    SlopeMeanResidualsMaxAdjusted,
)
from domain.value_objects.evaluation_values.slope_mean_residuals_min_adjusted import (
    SlopeMeanResidualsMinAdjusted,
)
from domain.value_objects.evaluation_values.slope_quadratic_residuals import (
    SlopeQuadraticResiduals,
)
from domain.value_objects.evaluation_values.slope_quadratic_residuals_max_adjusted import (
    SlopeQuadraticResidualsMaxAdjusted,
)
from domain.value_objects.evaluation_values.slope_quadratic_residuals_min_adjusted import (
    SlopeQuadraticResidualsMinAdjusted,
)


class ComputeSlitMeasurementEvaluationUseCase:
    """
    スリット光計測結果に対する評価値を算出する UseCase。

    評価軸は slit_source_z_coords（実空間 z）を使用する。
    """

    def execute(self, slope_result: SlopeComputationResult) -> MeasurementEvaluationResult:
        if slope_result.slope_angles.is_empty:
            raise ValueError("slope_angles is empty")
        if slope_result.slit_source_z_coords.is_empty:
            raise ValueError("slit_source_z_coords is empty")

        slopes = slope_result.slope_angles.slopes_in_world
        xs = slope_result.slit_source_z_coords.values.astype(np.float64)

        if slopes.shape[0] != xs.shape[0]:
            raise ValueError("slope count and slit_source_z_coords count do not match")

        ys_x = slopes[:, 0].astype(np.float64)
        ys_y = slopes[:, 1].astype(np.float64)

        linear_residuals = self._linear_residuals(xs, ys_x, ys_y)
        mean_residuals = self._mean_residuals(ys_x, ys_y)
        quadratic_residuals = self._quadratic_residuals(xs, ys_x, ys_y)

        linear_vo = SlopeLinearResiduals.create(linear_residuals)
        mean_vo = SlopeMeanResiduals.create(mean_residuals)
        quad_vo = SlopeQuadraticResiduals.create(quadratic_residuals)

        if not linear_vo or not mean_vo or not quad_vo:
            raise ValueError("failed to create residual value objects")

        linear_min_adjusted = linear_residuals - np.min(linear_residuals, axis=0)
        linear_max_adjusted = linear_residuals - np.max(linear_residuals, axis=0)

        mean_min_adjusted = mean_residuals - np.min(mean_residuals, axis=0)
        mean_max_adjusted = mean_residuals - np.max(mean_residuals, axis=0)

        quad_min_adjusted = quadratic_residuals - np.min(quadratic_residuals, axis=0)
        quad_max_adjusted = quadratic_residuals - np.max(quadratic_residuals, axis=0)

        linear_min_vo = SlopeLinearResidualsMinAdjusted.create(linear_min_adjusted)
        linear_max_vo = SlopeLinearResidualsMaxAdjusted.create(linear_max_adjusted)
        mean_min_vo = SlopeMeanResidualsMinAdjusted.create(mean_min_adjusted)
        mean_max_vo = SlopeMeanResidualsMaxAdjusted.create(mean_max_adjusted)
        quad_min_vo = SlopeQuadraticResidualsMinAdjusted.create(quad_min_adjusted)
        quad_max_vo = SlopeQuadraticResidualsMaxAdjusted.create(quad_max_adjusted)

        if not all([linear_min_vo, linear_max_vo, mean_min_vo, mean_max_vo, quad_min_vo, quad_max_vo]):
            raise ValueError("failed to create adjusted residual value objects")

        distortion_value = float(np.max(np.abs(quad_min_adjusted[:, 0])))
        slope_score_index = int(np.argmax(np.abs(quad_min_adjusted[:, 0])))
        distortion_vo = SlopeDistortionEvaluation(
            slope_score=distortion_value,
            slope_score_index=slope_score_index,
        )

        return MeasurementEvaluationResult(
            linear_residuals=linear_vo,
            mean_residuals=mean_vo,
            quadratic_residuals=quad_vo,
            linear_min_adjusted=linear_min_vo,
            linear_max_adjusted=linear_max_vo,
            mean_min_adjusted=mean_min_vo,
            mean_max_adjusted=mean_max_vo,
            quad_min_adjusted=quad_min_vo,
            quad_max_adjusted=quad_max_vo,
            slope_distortion=distortion_vo,
        )

    @staticmethod
    def _linear_residuals(xs: np.ndarray, ys_x: np.ndarray, ys_y: np.ndarray) -> np.ndarray:
        if xs.shape[0] < 2:
            pred_x = np.full_like(ys_x, np.mean(ys_x))
            pred_y = np.full_like(ys_y, np.mean(ys_y))
        else:
            coef_x = np.polyfit(xs, ys_x, 1)
            coef_y = np.polyfit(xs, ys_y, 1)
            pred_x = np.polyval(coef_x, xs)
            pred_y = np.polyval(coef_y, xs)

        return np.column_stack([ys_x - pred_x, ys_y - pred_y])

    @staticmethod
    def _mean_residuals(ys_x: np.ndarray, ys_y: np.ndarray) -> np.ndarray:
        mean_x = np.mean(ys_x)
        mean_y = np.mean(ys_y)
        return np.column_stack([ys_x - mean_x, ys_y - mean_y])

    @staticmethod
    def _quadratic_residuals(xs: np.ndarray, ys_x: np.ndarray, ys_y: np.ndarray) -> np.ndarray:
        if xs.shape[0] < 3:
            return ComputeSlitMeasurementEvaluationUseCase._linear_residuals(xs, ys_x, ys_y)

        coef_x = np.polyfit(xs, ys_x, 2)
        coef_y = np.polyfit(xs, ys_y, 2)
        pred_x = np.polyval(coef_x, xs)
        pred_y = np.polyval(coef_y, xs)
        return np.column_stack([ys_x - pred_x, ys_y - pred_y])

from __future__ import annotations
import numpy as np

from domain.aggregates.slope_computation_result import SlopeComputationResult
from domain.aggregates.measurement_evaluation_result import MeasurementEvaluationResult

# ★ 新しい残差評価サービス（LED world 座標版）
from domain.services.evaluation_services.slope_linear_residual_from_led_world_evaluation_service import (
    SlopeLinearResidualFromLedWorldEvaluationService,
)

# 6つの補正 VO
from domain.value_objects.evaluation_values.slope_linear_residuals_min_adjusted import (
    SlopeLinearResidualsMinAdjusted,
)
from domain.value_objects.evaluation_values.slope_linear_residuals_max_adjusted import (
    SlopeLinearResidualsMaxAdjusted,
)
from domain.value_objects.evaluation_values.slope_mean_residuals_min_adjusted import (
    SlopeMeanResidualsMinAdjusted,
)
from domain.value_objects.evaluation_values.slope_mean_residuals_max_adjusted import (
    SlopeMeanResidualsMaxAdjusted,
)
from domain.value_objects.evaluation_values.slope_quadratic_residuals_min_adjusted import (
    SlopeQuadraticResidualsMinAdjusted,
)
from domain.value_objects.evaluation_values.slope_quadratic_residuals_max_adjusted import (
    SlopeQuadraticResidualsMaxAdjusted,
)

# 歪み量 VO
from domain.value_objects.evaluation_values.slope_distortion_evaluation import (
    SlopeDistortionEvaluation,
)


class ComputeMeasurementEvaluationFromLedWorldUseCase:
    """
    LedWorldCoordinatesInFrame を用いて評価を行う UseCase。
    """

    def __init__(self) -> None:
        pass

    def execute(self, slope_result: SlopeComputationResult) -> MeasurementEvaluationResult:

        # ============================================================
        # ① 残差評価（DomainService: LED world 座標版）
        # ============================================================
        (
            linear_residuals_vo,
            mean_residuals_vo,
            quadratic_residuals_vo,
        ) = SlopeLinearResidualFromLedWorldEvaluationService.evaluate(
            slope_angles=slope_result.slope_angles,
            led_world_coords=slope_result.led_world_coordinates_in_frame,
        )

        # ============================================================
        # ② UseCase 内で追加処理（最小値・最大値補正）
        # ============================================================

        # --- 一次近似残差 ---
        linear_res = linear_residuals_vo.residuals
        linear_min_adjusted = linear_res - np.min(linear_res, axis=0)
        linear_max_adjusted = linear_res - np.max(linear_res, axis=0)

        linear_min_vo = SlopeLinearResidualsMinAdjusted.create(linear_min_adjusted)
        linear_max_vo = SlopeLinearResidualsMaxAdjusted.create(linear_max_adjusted)

        # --- 平均値残差 ---
        mean_res = mean_residuals_vo.residuals
        mean_min_adjusted = mean_res - np.min(mean_res, axis=0)
        mean_max_adjusted = mean_res - np.max(mean_res, axis=0)

        mean_min_vo = SlopeMeanResidualsMinAdjusted.create(mean_min_adjusted)
        mean_max_vo = SlopeMeanResidualsMaxAdjusted.create(mean_max_adjusted)

        # --- 二次近似残差 ---
        quad_res = quadratic_residuals_vo.residuals
        quad_min_adjusted = quad_res - np.min(quad_res, axis=0)
        quad_max_adjusted = quad_res - np.max(quad_res, axis=0)

        quad_min_vo = SlopeQuadraticResidualsMinAdjusted.create(quad_min_adjusted)
        quad_max_vo = SlopeQuadraticResidualsMaxAdjusted.create(quad_max_adjusted)

        # ============================================================
        # ③ 歪み量スコア（linear_min_adjusted の第一成分の最大値）
        # ============================================================

        distortion_value = float(np.max(np.abs(quad_min_adjusted[:, 0])))
        slope_score_index = int(np.argmax(np.abs(quad_min_adjusted[:, 0])))

        slope_distortion_vo = SlopeDistortionEvaluation(
            slope_score=distortion_value,
            slope_score_index=slope_score_index,
        )

        # ============================================================
        # ④ index を使って SlopeComputationResult から点を抽出
        # ============================================================

        red_point_in_frame = slope_result.red_bright_points_in_frame.coords_in_frame[slope_score_index]
        red_point_in_world = slope_result.red_bright_points_in_world.coords_in_world[slope_score_index]

        # ============================================================
        # ⑤ MeasurementEvaluationResult の生成（VO ベース）
        # ============================================================
        return MeasurementEvaluationResult(
            linear_residuals=linear_residuals_vo,
            mean_residuals=mean_residuals_vo,
            quadratic_residuals=quadratic_residuals_vo,

            linear_min_adjusted=linear_min_vo,
            linear_max_adjusted=linear_max_vo,

            mean_min_adjusted=mean_min_vo,
            mean_max_adjusted=mean_max_vo,

            quad_min_adjusted=quad_min_vo,
            quad_max_adjusted=quad_max_vo,

            slope_distortion=slope_distortion_vo,
        )

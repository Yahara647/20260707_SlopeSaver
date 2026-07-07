# src/application/usecases/compute_measurement_evaluation_usecase.py

from __future__ import annotations
import numpy as np

from domain.aggregates.slope_computation_result import SlopeComputationResult
from domain.aggregates.measurement_evaluation_result import MeasurementEvaluationResult

# 残差評価サービス
from domain.services.evaluation_services.slope_linear_residual_evaluation_service import (
    SlopeLinearResidualEvaluationService,
)

# 追加：6つの新しい VO
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
from domain.value_objects.evaluation_values.slope_distortion_evaluation import (
    SlopeDistortionEvaluation,
)


class ComputeMeasurementEvaluationUseCase:
    """
    SlopeComputationResult を入力として評価値を導出する UseCase。
    """

    def __init__(self) -> None:
        pass

    def execute(self, slope_result: SlopeComputationResult) -> MeasurementEvaluationResult:

        # ============================================================
        # ① 残差評価（DomainService）
        # ============================================================
        (
            linear_residuals_vo,
            mean_residuals_vo,
            quadratic_residuals_vo,
        ) = SlopeLinearResidualEvaluationService.evaluate(
            slope_angles=slope_result.slope_angles,
            red_points_world=slope_result.red_bright_points_in_world,
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

        # ここまでで 6 つの VO が生成されている：
        # linear_min_vo / linear_max_vo
        # mean_min_vo   / mean_max_vo
        # quad_min_vo   / quad_max_vo

        # ============================================================
        # ③ 歪み量スコア（linear_min_adjusted の第一成分の最大値）
        # ============================================================

        distortion_value = float(np.max(np.abs(linear_min_adjusted[:, 0])))
        slope_score_index = int(np.argmax(np.abs(linear_min_adjusted[:, 0])))

        # ============================================================
        # ★ 新しい VO を生成
        # ============================================================

        slope_distortion_vo = SlopeDistortionEvaluation(
            slope_score=distortion_value,
            slope_score_index=slope_score_index,
        )

        # ============================================================
        # ④ index を使って SlopeComputationResult から点を抽出
        # ============================================================

        red_point_in_frame = slope_result.red_bright_points_in_frame.coords_in_frame[slope_score_index]
        red_point_in_world = slope_result.red_bright_points_in_world.coords_in_world[slope_score_index]


        # ここまでで取得できている：
        # - slope_score（歪み量スコア）
        # - max_index（最大歪み点）
        # - red_point_in_frame（画像座標）
        # - red_point_in_world（世界座標）

        # ============================================================
        # ⑥ MeasurementEvaluationResult の生成（VO ベース）
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


    # ---------------------------------------------------------
    # 以下は仮の評価ロジック
    # ---------------------------------------------------------

    def _evaluate_slope_angles(self, linear_residuals_vo) -> float:
        return 1.0

    def _evaluate_strip_slopes(self, strip_slopes) -> float:
        return 1.0

    def _evaluate_red_points(self, red_points_world) -> float:
        return 1.0

    def _evaluate_normal_vectors(self, normal_vectors) -> float:
        return 1.0

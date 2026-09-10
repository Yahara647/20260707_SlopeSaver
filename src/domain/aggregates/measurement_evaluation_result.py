from __future__ import annotations
from dataclasses import dataclass

from domain.value_objects.evaluation_values.slope_linear_residuals import SlopeLinearResiduals
from domain.value_objects.evaluation_values.slope_mean_residuals import SlopeMeanResiduals
from domain.value_objects.evaluation_values.slope_quadratic_residuals import SlopeQuadraticResiduals

from domain.value_objects.evaluation_values.slope_linear_residuals_min_adjusted import SlopeLinearResidualsMinAdjusted
from domain.value_objects.evaluation_values.slope_linear_residuals_max_adjusted import SlopeLinearResidualsMaxAdjusted
from domain.value_objects.evaluation_values.slope_mean_residuals_min_adjusted import SlopeMeanResidualsMinAdjusted
from domain.value_objects.evaluation_values.slope_mean_residuals_max_adjusted import SlopeMeanResidualsMaxAdjusted
from domain.value_objects.evaluation_values.slope_quadratic_residuals_min_adjusted import SlopeQuadraticResidualsMinAdjusted
from domain.value_objects.evaluation_values.slope_quadratic_residuals_max_adjusted import SlopeQuadraticResidualsMaxAdjusted
from domain.value_objects.evaluation_values.slope_slit_frame_adjusted_linear_residuals import SlopeSlitFrameAdjustedLinearResiduals

from domain.value_objects.evaluation_values.slope_distortion_evaluation import SlopeDistortionEvaluation


@dataclass(frozen=True)
class MeasurementEvaluationResult:
    """
    計測結果に対する総合的な評価値を保持するアグリゲート。

    - 各種残差 VO（線形・平均・二次）
    - 最小値補正・最大値補正 VO
    - 歪み量評価 VO
    """

    # 元の残差
    linear_residuals: SlopeLinearResiduals
    mean_residuals: SlopeMeanResiduals
    quadratic_residuals: SlopeQuadraticResiduals

    # 最小値補正・最大値補正
    linear_min_adjusted: SlopeLinearResidualsMinAdjusted
    linear_max_adjusted: SlopeLinearResidualsMaxAdjusted

    mean_min_adjusted: SlopeMeanResidualsMinAdjusted
    mean_max_adjusted: SlopeMeanResidualsMaxAdjusted

    quad_min_adjusted: SlopeQuadraticResidualsMinAdjusted
    quad_max_adjusted: SlopeQuadraticResidualsMaxAdjusted

    # 歪み量評価
    slope_distortion: SlopeDistortionEvaluation

    # スリット画像座標の一次近似差を用いて補正した一次残差
    slit_frame_adjusted_linear_residuals: SlopeSlitFrameAdjustedLinearResiduals | None = None

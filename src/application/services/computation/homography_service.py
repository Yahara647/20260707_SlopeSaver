from logger.logger import logger

from domain.services.homography_transformer import HomographyTransformer
from domain.value_objects.computed_values.calibration_leds_in_frame import CalibrationLedsInFrame
from domain.value_objects.config_values.calibration_leds_in_world import CalibrationLedsInWorld
from domain.value_objects.computed_values.homography_matrix import HomographyMatrix
from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame
from domain.value_objects.computed_values.red_bright_points_in_world import RedBrightPointsInWorld


class HomographyService:
    """
    ホモグラフィ計算と座標変換をアプリケーション層で扱うサービス。
    Domain Service のラッパー。
    """

    def __init__(self, transformer: HomographyTransformer):
        self.transformer = transformer

    def compute_homography(
        self,
        calib_frame: CalibrationLedsInFrame,
        calib_world: CalibrationLedsInWorld
    ) -> HomographyMatrix:

        try:
            H = self.transformer.compute_homography(calib_frame, calib_world)
            logger.info("HomographyService: ホモグラフィ行列を生成しました")
            return H
        except Exception as e:
            logger.error(f"HomographyService: ホモグラフィ生成中に例外発生: {e}")
            raise

    def transform_red_points(
        self,
        H: HomographyMatrix,
        points_in_frame: RedBrightPointsInFrame,
        strip_z: float
    ) -> RedBrightPointsInWorld:

        try:
            world = self.transformer.transform_points(H, points_in_frame, strip_z)
            logger.debug("HomographyService: 輝点を世界座標へ変換しました")
            return world
        except Exception as e:
            logger.error(f"HomographyService: 座標変換中に例外発生: {e}")
            raise

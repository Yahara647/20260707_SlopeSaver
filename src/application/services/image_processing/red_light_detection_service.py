from domain.services.red_light_detector import RedLightDetector
from domain.entities.rgb8_frame import Rgb8Frame
from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame
from logger.logger import logger


class RedLightDetectionService:
    """
    RedLightDetector（Domain Service）をアプリケーション層でラップし、
    ログ・例外処理・パラメータ管理などを担当するサービス。
    """

    def __init__(self, detector: RedLightDetector):
        self.detector = detector

    def detect(self, frame: Rgb8Frame) -> RedBrightPointsInFrame:
        try:
            result = self.detector.execute(frame)
            if result.is_empty:
                logger.debug("RedLightDetectionService: 輝点なし")
            else:
                logger.debug(f"RedLightDetectionService: {len(result.coords_in_frame)} 点検出")
            return result

        except Exception as e:
            logger.error(f"RedLightDetectionService: 検出中に例外発生: {e}")
            return RedBrightPointsInFrame.create_empty()

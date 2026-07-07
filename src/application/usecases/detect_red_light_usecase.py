# src/application/usecases/detect_red_light_usecase.py

from application.services.image_processing.red_light_detection_service import RedLightDetectionService
from domain.entities.rgb8_frame import Rgb8Frame
from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame


class DetectRedLightUseCase:
    """
    1フレームから赤色輝点を検出するユースケース。
    """

    def __init__(self, detection_service: RedLightDetectionService):
        self.detection_service = detection_service

    def execute(self, frame: Rgb8Frame) -> RedBrightPointsInFrame:
        return self.detection_service.detect(frame)

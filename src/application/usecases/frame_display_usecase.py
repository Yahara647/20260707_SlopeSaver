from domain.entities.rgb8_frame import Rgb8Frame
from domain.value_objects.config_values.window_size import WindowSize
from application.services.display.frame_display_service import FrameDisplayService


class FrameDisplayUseCase:

    def __init__(self, display_service: FrameDisplayService):
        self.display_service = display_service

    def execute(
        self,
        frame: Rgb8Frame,
        window_name: str = "Camera",
        size: WindowSize | None = None
    ) -> bool:

        if frame is None:
            return False

        return self.display_service.show(
            frame=frame,
            window_name=window_name,
            size=size
        )

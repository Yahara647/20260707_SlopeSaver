import cv2
from domain.entities.rgb8_frame import Rgb8Frame
from domain.value_objects.config_values.window_size import WindowSize


class FrameDisplayService:

    def show(
        self,
        frame: Rgb8Frame,
        window_name: str = "Camera",
        size: WindowSize | None = None
    ) -> bool:

        if frame is None:
            return False

        image = frame.data

        # --- WindowSize が指定されていればリサイズ ---
        if size is not None:
            image = cv2.resize(image, size.as_tuple())

        cv2.imshow(window_name, image)
        cv2.waitKey(1)
        return True

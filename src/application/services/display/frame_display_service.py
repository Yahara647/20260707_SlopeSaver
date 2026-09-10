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

        if image.ndim == 2:
            display_image = image
        elif image.ndim == 3 and image.shape[2] == 3:
            display_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        else:
            return False

        if size is not None:
            display_image = cv2.resize(display_image, size.as_tuple())

        cv2.imshow(window_name, display_image)
        cv2.waitKey(1)
        return True

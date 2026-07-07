from __future__ import annotations

from pathlib import Path
from datetime import datetime
from logger.logger import logger

from domain.interfaces.i_camera_service import ICameraService
from domain.value_objects.config_values.exposure_for_computation import ExposureForComputation

from application.services.camera.camera_capture_service import CameraCaptureService

from PIL import Image


class SavePictureUseCase:
    """
    ExposureForComputation を使って撮像し、
    base_dir/YYYYMMDD/picture/ に YYYYMMDD_HHMMSS.png を保存する UseCase。
    """

    def __init__(self, camera_service: ICameraService) -> None:
        self._logger = logger
        self._camera_capture_service = CameraCaptureService(
            camera_service=camera_service,
            camera_state=camera_service.state,
            logger=logger
        )

    def execute(self, base_dir: str, exposure: ExposureForComputation) -> Path | None:

        # --- 撮像 ---
        frame = self._camera_capture_service.capture_with_exposure(exposure.value)
        if frame is None:
            self._logger.error("SavePictureUseCase: 撮像に失敗")
            return None

        # --- ★ Rgb8Frame → PIL.Image に変換 ---
        try:
            np_img = frame.data  # ★ numpy.ndarray
            # ★ BGR → RGB 変換
            np_img = np_img[:, :, ::-1]
            pil_img = Image.fromarray(np_img)
        except Exception as e:
            self._logger.error(f"SavePictureUseCase: 画像変換に失敗: {e}")
            return None

        # --- フォルダ構成 ---
        now = datetime.now()
        date_dir = Path(base_dir) / now.strftime("%Y%m%d") / "picture"
        date_dir.mkdir(parents=True, exist_ok=True)

        save_path = date_dir / f"{now:%Y%m%d_%H%M%S}.png"

        # --- 保存 ---
        try:
            pil_img.save(str(save_path))
            self._logger.info(f"SavePictureUseCase: Saved → {save_path}")
            return save_path
        except Exception as e:
            self._logger.error(f"SavePictureUseCase: 保存に失敗: {e}")
            return None

# src/application/usecases/high_exposure_capture_usecase.py

from __future__ import annotations
import time

from domain.interfaces.i_camera_service import ICameraService
from application.buffers.frame_buffer import FrameBuffer
from domain.aggregates.app_config import AppConfig

from logger.logger import logger


class HighExposureCaptureUseCase:
    """
    高露光撮像を行うアプリケーション層の UseCase。
    撮像処理自体は Infra 層の camera.capture_with_exposure() に委譲し、
    本クラスは「撮像フロー」と「停止制御」だけを担当する。
    """

    def __init__(
        self,
        camera: ICameraService,
        buffer: FrameBuffer,
        app_config: AppConfig,   # ★ AppConfig を受け取る
    ) -> None:
        self._camera = camera
        self._buffer = buffer
        self._app_config = app_config
        self._logger = logger

        self._running: bool = False

    # ------------------------------------------------------------
    # 撮像ループ
    # ------------------------------------------------------------
    def run(self) -> None:
        self._logger.info("HighExposureCaptureUseCase: 撮像ループ開始")
        self._running = True

        while self._running:

            # ★ 最新の露光値を AppConfig から取得
            exposure_us = self._app_config.exposure_for_display.value

            # ★ 最新露光で撮像（捨てフレーム込み）
            frame = self._camera.capture_with_exposure(exposure_us)

            if frame is None:
                self._logger.warning("HighExposureCaptureUseCase: 撮像失敗（frame=None）")
                continue

            self._buffer.push(frame)
            time.sleep(0.005)

        self._logger.info("HighExposureCaptureUseCase: 撮像ループ終了")

    # ------------------------------------------------------------
    # 停止要求
    # ------------------------------------------------------------
    def stop(self) -> None:
        self._logger.info("HighExposureCaptureUseCase: 停止要求を受け取りました")
        self._running = False

# src/presentation/threads/high_exposure_thread.py

from __future__ import annotations

from threading import Thread
from typing import Optional

from application.usecases.high_exposure_capture_usecase import HighExposureCaptureUseCase
from logger.logger import logger


class HighExposureThread:
    """
    高露光撮像用のスレッド管理クラス（Presentation 層）。
    撮像ロジック自体は UseCase に委譲し、
    ここでは「別スレッドで動かすこと」だけを担当する。
    """

    def __init__(self, usecase: HighExposureCaptureUseCase) -> None:
        self._usecase = usecase
        self._thread: Optional[Thread] = None
        self._logger = logger

    def start(self) -> None:
        if self._thread is not None:
            return

        self._logger.info("HighExposureThread: start() called")

        self._thread = Thread(
            target=self._usecase.run,
            daemon=True,
            name="HighExposureCaptureThread",
        )
        self._thread.start()

    def stop(self) -> None:
        self._logger.info("HighExposureThread: stop() called")
        self._usecase.stop()

    def join(self, timeout: float | None = None) -> None:
        if self._thread is not None:
            self._logger.info("HighExposureThread: join() called")
            self._thread.join(timeout)

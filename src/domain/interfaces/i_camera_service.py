# src/domain/interfaces/i_camera_service.py

from abc import ABC, abstractmethod
from domain.entities.rgb8_frame import Rgb8Frame


class ICameraService(ABC):

    @abstractmethod
    def initialize(self) -> bool:
        pass

    @abstractmethod
    def capture(self) -> Rgb8Frame | None:
        pass

    @abstractmethod
    def capture_with_exposure(self, exposure_us: float) -> Rgb8Frame | None:
        """
        指定露光で1枚撮像し、撮像後に元の露光に戻す。
        露光変更と撮像を同一ロック内で行う。
        """
        pass

    @abstractmethod
    def close(self) -> None:
        pass

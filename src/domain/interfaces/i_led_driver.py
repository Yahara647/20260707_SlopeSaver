from abc import ABC, abstractmethod

class ILedDriver(ABC):

    @abstractmethod
    def initialize(self) -> bool:
        pass

    @abstractmethod
    def set_led(self, led_id: int, state: bool) -> bool:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def get_led_count(self) -> int:
        pass

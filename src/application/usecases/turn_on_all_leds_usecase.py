from application.services.led.led_control_service import LedControlService
from logging import Logger


class TurnOnAllLedsUseCase:

    def __init__(self, led_control_service: LedControlService, logger: Logger):
        self.led_control_service = led_control_service
        self.logger = logger

    def execute(self) -> bool:
        self.logger.info("UseCase: 全 LED 点灯開始")
        return self.led_control_service.turn_on_all()

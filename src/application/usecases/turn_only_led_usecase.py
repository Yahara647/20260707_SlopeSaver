from application.services.led.led_control_service import LedControlService

class TurnOnlyLedUseCase:

    def __init__(self, led_service: LedControlService):
        self.led_service = led_service

    def execute(self, led_id: int) -> bool:
        """指定した LED を 1 つだけ点灯させる"""
        return self.led_service.turn_only(led_id)

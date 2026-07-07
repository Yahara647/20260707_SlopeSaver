from domain.interfaces.i_led_driver import ILedDriver

class LedInitializeUseCase:

    def __init__(self, led_driver: ILedDriver):
        self.led_driver = led_driver

    def execute(self) -> bool:
        """LED 初期化を実行する"""
        return self.led_driver.initialize()

from domain.interfaces.i_led_driver import ILedDriver
from logging import Logger


class LedControlService:

    def __init__(self, led_driver: ILedDriver, logger: Logger):
        self.led_driver = led_driver
        self.logger = logger

    def turn_only(self, led_id: int) -> bool:
        """指定した LED だけを点灯させる"""
        self.logger.info(f"LedControlService: LED {led_id} のみ点灯開始")

        # まず全て OFF
        for i in range(self.led_driver.state.output_num):
            if not self.led_driver.set_led(i, False):
                self.logger.error(f"LedControlService: LED {i} の OFF に失敗")
                return False

        # 指定 LED を ON
        result = self.led_driver.set_led(led_id, True)

        if result:
            self.logger.info(f"LedControlService: LED {led_id} のみ点灯成功")
        else:
            self.logger.error(f"LedControlService: LED {led_id} の点灯に失敗")

        return result

    def turn_on_all(self) -> bool:
        """すべての LED を点灯"""
        self.logger.info("LedControlService: 全 LED 点灯開始")

        for i in range(self.led_driver.state.output_num):
            if not self.led_driver.set_led(i, True):
                self.logger.error(f"LedControlService: LED {i} の点灯に失敗")
                return False

        self.logger.info("LedControlService: 全 LED 点灯成功")
        
        return True

    def turn_off_all(self) -> bool:
        """すべての LED を消灯"""
        self.logger.info("LedControlService: 全 LED 消灯開始")

        for i in range(self.led_driver.state.output_num):
            if not self.led_driver.set_led(i, False):
                self.logger.error(f"LedControlService: LED {i} の消灯に失敗")
                return False

        self.logger.info("LedControlService: 全 LED 消灯成功")
        return True

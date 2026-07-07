import time
from logging import Logger


class LedStabilizeService:

    def __init__(self, logger: Logger):
        self.logger = logger

    def wait_until_stable(self, led_id: int) -> bool:
        """LED が安定して点灯するまで待つ（暫定：0.05 秒固定）"""

        self.logger.info(f"LedStabilizeService: LED {led_id} の安定待ち開始（0.05 秒）")

        time.sleep(0.15)

        self.logger.info(f"LedStabilizeService: LED {led_id} の安定待ち完了")

        return True

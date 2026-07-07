from pymodbus.client import ModbusTcpClient
from domain.interfaces.i_led_driver import ILedDriver
from infrastructure.dio.dio_state import DioState
from src.logger.logger import logger
import threading
import time


class DioLedDriver(ILedDriver):

    def __init__(self, state: DioState):
        self.state: DioState = state
        self.client: ModbusTcpClient | None = None

        # 排他制御
        self._lock = threading.Lock()
        self._is_writing = False

    def initialize(self) -> bool:
        try:
            self.client = ModbusTcpClient(
                self.state.host,
                timeout=self.state.timeout
            )

            if not self.client.connect():
                logger.error("DioLedDriver: Modbus 接続に失敗しました")
                return False

            logger.info("DioLedDriver: Modbus 接続成功")

            # 全 LED OFF
            for i in range(self.state.output_num):
                self.client.write_coil(i, False)

            logger.info("DioLedDriver: 全 LED を OFF に初期化しました")
            return True

        except Exception as e:
            logger.error(f"DioLedDriver: 初期化中に例外発生: {e}")
            return False

    def set_led(self, led_id: int, state: bool) -> bool:
        if self.client is None:
            logger.error("DioLedDriver: 初期化されていません")
            return False

        if not (0 <= led_id < self.state.output_num):
            logger.error(f"DioLedDriver: led_id {led_id} は範囲外です")
            return False

        # 排他制御
        while True:
            with self._lock:
                if not self._is_writing:
                    self._is_writing = True
                    break
            time.sleep(0.0005)

        try:
            rr = self.client.write_coil(led_id, bool(state))
            if rr.isError():
                logger.error(f"DioLedDriver: write_coil({led_id}, {state}) に失敗")
                return False

            logger.info(f"DioLedDriver: LED {led_id} → {state}")
            return True

        except Exception as e:
            logger.error(f"DioLedDriver: set_led 中に例外発生: {e}")
            return False

        finally:
            with self._lock:
                self._is_writing = False

    def get_led_count(self) -> int:
        return self.state.output_num

    def close(self) -> None:
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass

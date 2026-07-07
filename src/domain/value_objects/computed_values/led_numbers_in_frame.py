# src/domain/value_objects/computed_values/led_numbers_in_frame.py

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class LedNumbersInFrame:
    """
    画像内で検出された LED 番号の集合を保持する ValueObject。

    - led_nums: shape = (N,), dtype = int32
                LED 番号の配列（昇順であることが望ましい）
    """

    led_nums: np.ndarray  # shape = (N,), int32

    @property
    def is_empty(self) -> bool:
        """LED 番号が 1 つも存在しない場合 True"""
        return self.led_nums is None or len(self.led_nums) == 0

    @classmethod
    def create(cls, led_nums: np.ndarray) -> "LedNumbersInFrame | False":
        """
        led_nums を安全に格納するファクトリメソッド。

        - led_nums: NumPy ndarray, shape=(N,), dtype=int32
        """

        # --- 型チェック ---
        if not isinstance(led_nums, np.ndarray):
            return False

        # --- dtype チェック ---
        if led_nums.dtype != np.int32:
            return False

        # --- shape チェック ---
        if led_nums.ndim != 1:
            return False

        # 不変性のためコピーして保持
        return cls(led_nums=led_nums.copy())

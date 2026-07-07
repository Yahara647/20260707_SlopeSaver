# src/application/buffers/frame_buffer.py

from __future__ import annotations

import collections
import threading
import numpy as np

from domain.entities.rgb8_frame import Rgb8Frame
from logger.logger import logger


class FrameBuffer:
    """
    Rgb8Frame を保持するスレッド安全なバッファ。
    - push() はコピーして安全に格納
    - pop() はコピーして返す（従来）
    - pop_raw() はコピーせず返す（高速表示用）
    """

    def __init__(self, max_size: int = 10):
        self.buffer = collections.deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._logger = logger

    def push(self, frame: Rgb8Frame) -> None:
        """Rgb8Frame をバッファに追加する（コピーして安全に保持）"""
        if not isinstance(frame, Rgb8Frame):
            raise TypeError("frame は Rgb8Frame 型である必要があります")

        copied = Rgb8Frame(
            data=np.copy(frame.data),
            timestamp=frame.timestamp
        )

        with self._lock:
            self.buffer.append(copied)
            self._logger.debug(f"FrameBuffer: push() size={len(self.buffer)}")

    def pop(self) -> Rgb8Frame:
        """
        最初に追加された Rgb8Frame を返し、バッファから削除する。
        data はコピーして返す（安全だが遅い）。
        """
        with self._lock:
            if len(self.buffer) == 0:
                raise IndexError("バッファが空です")

            original: Rgb8Frame = self.buffer.popleft()
            self._logger.debug(f"FrameBuffer: pop() size={len(self.buffer)}")

            return Rgb8Frame(
                data=np.copy(original.data),
                timestamp=original.timestamp
            )

    def pop_raw(self) -> Rgb8Frame:
        """
        最初に追加された Rgb8Frame を返し、バッファから削除する。
        data をコピーしないため高速。表示用途に使用する。
        """
        with self._lock:
            if len(self.buffer) == 0:
                raise IndexError("バッファが空です")

            frame = self.buffer.popleft()
            self._logger.debug(f"FrameBuffer: pop_raw() size={len(self.buffer)}")

            return frame  # ← コピーしない

    def peek(self) -> Rgb8Frame:
        """最後に追加された Rgb8Frame をコピーして返す（削除しない）"""
        with self._lock:
            if len(self.buffer) == 0:
                raise IndexError("バッファが空です")

            original: Rgb8Frame = self.buffer[-1]

            return Rgb8Frame(
                data=np.copy(original.data),
                timestamp=original.timestamp
            )

    def is_empty(self) -> bool:
        with self._lock:
            return len(self.buffer) == 0

    def size(self) -> int:
        with self._lock:
            return len(self.buffer)

    def clear(self) -> None:
        with self._lock:
            self.buffer.clear()
            self._logger.debug("FrameBuffer: clear()")

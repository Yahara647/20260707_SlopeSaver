# src/presentation/threads/display_thread.py

from __future__ import annotations

import numpy as np
import cv2
import time
from threading import Thread
from typing import Optional

from application.buffers.frame_buffer import FrameBuffer
from domain.value_objects.config_values.app_flags import AppFlags
from logger.logger import logger
from domain.aggregates.app_config import AppConfig 
from shared.shared_evaluation import shared_evaluation
from shared.shared_graph_data import shared_graph_data


class DisplayThread:
    """
    FrameBuffer から取得したフレームを OpenCV で表示するスレッド。
    表示処理とスレッド管理のみを担当する。
    FPS 制御 + waitKey により GUI の安定性を確保する。
    busy loop を完全に排除し、固まりを防止する。
    """

    def __init__(
        self,
        buffer: FrameBuffer,
        app_config: AppConfig,
        window_name: str = "display",
        fps_limit: int = 20,
        window_size: tuple[int, int] = (800, 600),   # ★追加：表示ウィンドウのサイズ
    ) -> None:
        self.buffer = buffer
        self.app_config = app_config
        self.window_name = window_name
        self.fps_limit = fps_limit
        self.window_size = window_size              # ★追加

        self._thread: Optional[Thread] = None
        self._logger = logger

        # FPS 制御用
        self._last_time = time.time()
        self._last_highlight_update = time.time()
        self._last_graph_update = time.time()
        self._cached_point = None
        self._cached_score = None
        self._graph_window_open = False


    def start(self) -> None:
        """表示スレッドを開始する"""
        if self._thread is not None:
            return
        
        time.sleep(1)

        self._logger.info("DisplayThread: start()")

        self._thread = Thread(
            target=self.run,
            daemon=True,
            name="DisplayThread",
        )
        self._thread.start()

    def run(self) -> None:
        self._logger.info("DisplayThread: run() started")

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.window_size[0], self.window_size[1])

        # cv2.namedWindow("graph_display", cv2.WINDOW_NORMAL)
        # cv2.resizeWindow("graph_display", 600, 400)

        try:
            while True:
                try:
                    # --- 終了フラグ ---
                    if self.app_config.app_flags.shutdown:
                        self._logger.info("DisplayThread: shutdown detected")
                        break

                    # --- FPS 制御 ---
                    now = time.time()
                    interval = 1.0 / self.fps_limit
                    sleep_time = interval - (now - self._last_time)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    self._last_time = time.time()

                    # --- バッファが空 ---
                    if self.buffer.is_empty():
                        cv2.waitKey(1)
                        continue

                    # --- フレーム取得 ---
                    frame_item = self.buffer.pop_raw()
                    if frame_item is None or frame_item.data is None:
                        self._logger.warning("DisplayThread: frame_item is None")
                        continue

                    frame = frame_item.data

                    # --- tiny sleep ---
                    time.sleep(0.0005)

                    # --- ハイライト描画 ---
                    if self.app_config.app_flags.highlight_enabled:
                        now = time.time()
                        if now - self._last_highlight_update >= 1.0:
                            with shared_evaluation.lock:
                                self._cached_point = shared_evaluation.highlight_point
                                self._cached_score = shared_evaluation.slope_score
                            self._last_highlight_update = now

                        if self._cached_point is not None:
                            cv2.circle(frame, self._cached_point, 10, (0, 255, 0), 2)

                        if self._cached_score is not None:
                            score = max(0.0, min(1.0, self._cached_score))
                            bar_length = int(score * 200)
                            cv2.rectangle(frame, (10, 10), (210, 40), (50, 50, 50), -1)
                            cv2.rectangle(frame, (10, 10), (10 + bar_length, 40), (0, 255, 0), -1)
                            cv2.putText(frame, f"Score: {self._cached_score:.4f}",
                                        (220, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

                    # --- 映像表示 ---
                    cv2.imshow(self.window_name, frame)
                    cv2.waitKey(1)

                    # --- グラフ描画（1秒に1回 & ボタンON） ---
                    if self.app_config.app_flags.graph_enabled:

                        # ★ ウィンドウがまだ開いていなければ作成
                        if not self._graph_window_open:
                            cv2.namedWindow("graph_display", cv2.WINDOW_NORMAL)
                            cv2.resizeWindow("graph_display", 600, 400)
                            self._graph_window_open = True

                        now = time.time()
                        if now - self._last_graph_update >= 1.0:

                            with shared_graph_data.lock:
                                red_world = shared_graph_data.red_in_world
                                residuals = shared_graph_data.slope_linear_residuals_min_adjusted

                            if red_world is not None and residuals is not None:
                                graph_img = np.zeros((400, 600, 3), dtype=np.uint8)

                                xs = red_world[:, 1]
                                ys = residuals[:, 0]

                                if len(xs) > 1:
                                    xs_norm = ((xs - xs.min()) / (xs.max() - xs.min() + 1e-6)) * 580 + 10
                                    ys_ratio = ys
                                    ys_norm = 380 - (ys_ratio * 380) + 10

                                    for i in range(1, len(xs_norm)):
                                        cv2.line(
                                            graph_img,
                                            (int(xs_norm[i-1]), int(ys_norm[i-1])),
                                            (int(xs_norm[i]), int(ys_norm[i])),
                                            (0, 255, 0),
                                            2
                                        )

                                cv2.imshow("graph_display", graph_img)

                            self._last_graph_update = now

                    else:
                        # ★ グラフOFF → ウィンドウを閉じる
                        if self._graph_window_open:
                            try:
                                cv2.destroyWindow("graph_display")
                            except Exception as e:
                                self._logger.error(f"Failed to destroy graph window: {e}")
                            self._graph_window_open = False


                except Exception as e:
                    self._logger.error(f"DisplayThread loop error: {e}")
                    time.sleep(0.1)
                    continue

        except Exception as e:
            self._logger.error(f"DisplayThread fatal error: {e}")

        self._logger.info("DisplayThread: run() finished")

    def stop(self) -> None:
        self._logger.info("DisplayThread: stop()")
        self.app_config.app_flags = AppFlags(
            shutdown=True,
            pause=self.app_config.app_flags.pause,
            display_enabled=self.app_config.app_flags.display_enabled,
        )

    def join(self, timeout: float | None = None) -> None:
        """スレッド終了を待機する"""
        if self._thread is not None:
            self._logger.info("DisplayThread: join()")
            self._thread.join(timeout)

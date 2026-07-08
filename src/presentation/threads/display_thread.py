# src/presentation/threads/display_thread.py

from __future__ import annotations

import numpy as np
import cv2
import time
from threading import Thread
from typing import Optional
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

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
        self._graph_plot_rect = (105, 185, 495, 388)
        self._graph_base_template = self._load_graph_base_template()

    def _load_graph_base_template(self) -> np.ndarray:
        """グラフ背景のテンプレート画像を読み込む。"""
        template_path = (
            Path(__file__).resolve().parents[3]
            / "output"
            / "graph_assets"
            / "base_graph_template.png"
        )

        template = cv2.imread(str(template_path))
        if template is None:
            self._logger.warning(f"Graph template not found: {template_path}")
            return np.full((400, 600, 3), 255, dtype=np.uint8)

        if template.shape[:2] != (400, 600):
            template = cv2.resize(template, (600, 400), interpolation=cv2.INTER_AREA)

        return template

    def _draw_japanese_text(self, img: np.ndarray, text: str, position: tuple, font_size: int = 14, color: tuple = (0, 0, 0)) -> np.ndarray:
        """
        OpenCV画像にPILで日本語テキストを描画する。
        
        Args:
            img: OpenCV形式の画像（BGR）
            text: 描画するテキスト（日本語対応）
            position: (x, y) テキスト描画位置
            font_size: フォントサイズ
            color: (B, G, R) 色
        
        Returns:
            テキストが描画された画像
        """
        # BGR → RGB に変換
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # PIL Imageに変換
        img_pil = Image.fromarray(img_rgb)
        draw = ImageDraw.Draw(img_pil)
        
        # Windowsの日本語フォント（MSゴシック）を指定
        try:
            font_path = "C:\\Windows\\Fonts\\msgothic.ttc"
            font = ImageFont.truetype(font_path, font_size)
        except:
            # フォントが見つからない場合はデフォルトフォントを使用
            font = ImageFont.load_default()
        
        # RGB形式で色を指定（RGB）
        color_rgb = (color[2], color[1], color[0])
        
        # テキストを描画
        draw.text(position, text, font=font, fill=color_rgb)
        
        # RGB → BGRに変換してOpenCV形式に戻す
        img_rgb = np.array(img_pil)
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        
        return img_bgr

    _REGION_THRESHOLD = 0.5

    def _render_graph_overlay(self, red_world: np.ndarray, residuals: np.ndarray) -> np.ndarray:
        """背景テンプレート上にグラフ領域だけ折れ線を重ねて描画する。"""
        graph_img = self._graph_base_template.copy()
        y_axis_max = 1.0

        ys_all = residuals[:, 0]
        data_max = float(np.max(ys_all)) if len(ys_all) > 0 else 0.0

        # 画像左上に、グラフ縦軸データの最大値を Score として表示
        score_text = f"Score: {data_max:.4f}"
        cv2.putText(
            graph_img,
            score_text,
            (12, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (40, 40, 40),
            2,
            cv2.LINE_AA,
        )

        x1, y1, x2, y2 = self._graph_plot_rect
        margin = 8
        plot_x1, plot_y1 = x1 + margin, y1 + margin
        plot_x2, plot_y2 = x2 - margin, y2 - margin

        xs = red_world[:, 1]
        ys = residuals[:, 0]

        if len(xs) <= 1:
            return graph_img

        x_span = xs.max() - xs.min()
        if x_span < 1e-9:
            xs_norm = np.full(len(xs), (plot_x1 + plot_x2) / 2.0)
        else:
            xs_norm = ((xs - xs.min()) / x_span) * (plot_x2 - plot_x1) + plot_x1

        ys_clamped = np.clip(ys, 0.0, y_axis_max)
        ys_norm = plot_y2 - ys_clamped / y_axis_max * (plot_y2 - plot_y1)

        for i in range(1, len(xs_norm)):
            p1 = (int(xs_norm[i - 1]), int(ys_norm[i - 1]))
            p2 = (int(xs_norm[i]), int(ys_norm[i]))
            cv2.line(graph_img, p1, p2, (0, 200, 0), 2)

        # --- 3分割領域ごとの最大値を計算して描画 ---
        plot_width = plot_x2 - plot_x1
        region_borders_px = [
            plot_x1,
            plot_x1 + plot_width // 3,
            plot_x1 + 2 * plot_width // 3,
            plot_x2,
        ]

        # 境界線（点線）を描画
        dash_len, gap_len = 6, 4
        for bx in region_borders_px[1:2] + region_borders_px[2:3]:
            y_cur = plot_y1
            while y_cur < plot_y2:
                y_end = min(y_cur + dash_len, plot_y2)
                cv2.line(graph_img, (bx, y_cur), (bx, y_end), (120, 120, 120), 1)
                y_cur += dash_len + gap_len

        # 領域ラベル定義
        region_labels = ["D伸び", "中伸び", "W伸び"]

        for region_idx in range(3):
            bx_left = region_borders_px[region_idx]
            bx_right = region_borders_px[region_idx + 1]

            # この領域に含まれるデータ点のインデックス
            in_region = np.where((xs_norm >= bx_left) & (xs_norm < bx_right))[0]
            if len(in_region) == 0:
                continue

            region_max = float(np.max(ys[in_region]))
            region_max_idx = in_region[int(np.argmax(ys[in_region]))]

            # 境界上の最大値かどうかを判定（隣接領域境界±1px以内）
            at_boundary = False
            px = float(xs_norm[region_max_idx])
            if region_idx in (0, 1):
                boundary_px = float(region_borders_px[region_idx + 1])
                if abs(px - boundary_px) <= 1:
                    at_boundary = True

            # 色選択：閾値超え かつ 境界上でない → 赤
            if region_max > self._REGION_THRESHOLD and not at_boundary:
                text_color = (0, 0, 220)
            else:
                text_color = (40, 40, 40)

            # テキスト中央位置
            text_cx = int((bx_left + bx_right) / 2)

            # ★ ラベルテキスト（領域名）を描画（数値の上側）
            label_text = region_labels[region_idx]
            graph_img = self._draw_japanese_text(
                graph_img,
                label_text,
                (text_cx - 20, plot_y1 - 40),
                font_size=14,
                color=text_color,
            )

            # 最大値テキストをグラフ領域の上側に描画
            cv2.putText(
                graph_img,
                f"{region_max:.2f}",
                (text_cx - 22, plot_y1 - 14),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                text_color,
                1,
                cv2.LINE_AA,
            )

        return graph_img


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
                            cv2.namedWindow("Steel_Strip_Profile", cv2.WINDOW_NORMAL)
                            cv2.resizeWindow("Steel_Strip_Profile", 600, 400)
                            self._graph_window_open = True

                        now = time.time()
                        if now - self._last_graph_update >= 1.0:

                            with shared_graph_data.lock:
                                red_world = shared_graph_data.red_in_world
                                residuals = shared_graph_data.slope_linear_residuals_min_adjusted

                            if red_world is not None and residuals is not None:
                                graph_img = self._render_graph_overlay(red_world, residuals)

                                cv2.imshow("Steel_Strip_Profile", graph_img)

                            self._last_graph_update = now

                    else:
                        # ★ グラフOFF → ウィンドウを閉じる
                        if self._graph_window_open:
                            try:
                                cv2.destroyWindow("Steel_Strip_Profile")
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

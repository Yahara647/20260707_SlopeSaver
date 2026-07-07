# src/presentation/gui/views/camera_setting_view.py

from __future__ import annotations
import dearpygui.dearpygui as dpg

from presentation.gui.controllers.camera_setting_controller import CameraSettingController


class CameraSettingView:
    """
    カメラ設定（露光・ゲインなど）を行う画面。
    UI の見た目だけを担当し、処理は CameraSettingController に委譲する。
    """

    def __init__(self, controller: CameraSettingController) -> None:
        self.controller = controller

    # ---------------------------------------------------------
    # ★ キャリブレーション：AppConfig の表示用露光を使用
    # ---------------------------------------------------------
    def _on_calibrate(self) -> None:
        exposure = float(self.controller.config.exposure_for_display.value)
        self.controller.on_calibrate_homography(exposure_us=exposure)

    # ---------------------------------------------------------
    # ★ ROI 設定：AppConfig の表示用露光を使用
    # ---------------------------------------------------------
    def _on_set_roi(self) -> None:
        exposure = float(self.controller.config.exposure_for_display.value)
        self.controller.on_set_roi(exposure_us=exposure)

    # ---------------------------------------------------------
    # ★ UI 描画
    # ---------------------------------------------------------
    def render(self) -> None:

        cfg = self.controller.config
        cam_state = self.controller.camera_service.state

        dpg.add_text("【設定】")
        dpg.add_text("　・前回の設定がそのまま反映されています")
        dpg.add_text("　・通常は操作必要ありません")
        dpg.add_text("　・必要なときのみ修正してください")
        dpg.add_spacer(height=5)
        dpg.add_separator()

        # --- 表示用露光 ---
        dpg.add_spacer(height=5)
        dpg.add_text("a. 明るさ設定")

        dpg.add_text("　ⅰ. ディスプレイ映像 明るさ（露光時間:us）")
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_input_int(
                tag="display_exposure_input",
                default_value=int(cfg.exposure_for_display.value),
                min_value=1,
                max_value=1_000_000,
                width=200,
            )

        # --- 計算用露光 ---
        dpg.add_text("　ⅱ. 測定用映像 明るさ（露光時間:us）")
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_input_int(
                tag="compute_exposure_input",
                default_value=int(cfg.exposure_for_computation.value),
                min_value=1,
                max_value=1_000_000,
                width=200,
            )

        # --- Apply All Settings ---
        dpg.add_text("　ⅲ. 設定を適用")
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_button(
                label="click",
                width=200,
                callback=lambda: self.controller.on_apply_all_settings(
                    display_exp=dpg.get_value("display_exposure_input"),
                    compute_exp=dpg.get_value("compute_exposure_input"),
                )
            )
        dpg.add_spacer(height=10)
        dpg.add_separator()

        # --- ROI 設定 ---
        dpg.add_spacer(height=5)
        dpg.add_text("b. カメラ描画範囲を変更（カメラ位置・角度変更時に使用）")
        dpg.add_spacer(height=5)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_button(
                tag="set_roi_button",
                label="click",
                width=200,
                callback=self._on_set_roi
            )
        dpg.add_spacer(height=10)
        dpg.add_separator()

        # --- ホモグラフィ導出 ---
        dpg.add_spacer(height=5)
        dpg.add_text("c. 座標の校正（カメラ位置・角度変更時に使用）")
        dpg.add_spacer(height=5)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_button(
                tag="calibrate_homography_button",
                label="click",
                width=200,
                callback=self._on_calibrate
            )

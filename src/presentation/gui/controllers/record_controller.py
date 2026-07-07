# src/presentation/gui/controllers/record_controller.py

from __future__ import annotations

from domain.aggregates.app_config import AppConfig
from domain.value_objects.config_values.app_flags import AppFlags
from infrastructure.camera.pylon_camera_driver import PylonCameraDriver
from infrastructure.dio.dio_led_driver import DioLedDriver

import dearpygui.dearpygui as dpg


class RecordController:
    """
    RecordView の操作を受け取るが、
    現段階では何の処理も行わない最小構成のコントローラ。
    """

    def __init__(
        self,
        config: AppConfig,
        camera_service: PylonCameraDriver,
        dio_service: DioLedDriver,
    ) -> None:
        self.config = config
        self.camera_service = camera_service
        self.dio_service = dio_service

        # 排他トグルの状態
        self.save_image_only = False
        self.save_all = False

    # ---------------------------------------------------------
    # 保存モード（排他トグル）
    # ---------------------------------------------------------
    def on_toggle_save_image(self, this_btn: str, other_btn: str) -> None:
        self.save_image_only = not self.save_image_only
        self.save_all = False

        # UI 更新
        dpg.set_item_label(this_btn, f"Save Image Only ({'ON' if self.save_image_only else 'OFF'})")
        dpg.set_item_label(other_btn, "Save Image + Result (OFF)")

        # ★ AppFlags に反映
        self.config.app_flags = AppFlags(
            shutdown=self.config.app_flags.shutdown,
            pause=self.config.app_flags.pause,
            display_enabled=self.config.app_flags.display_enabled,
            save_mode="image_only" if self.save_image_only else "none",
        )


    def on_toggle_save_all(self, this_btn: str) -> None:
        self.save_all = not self.save_all
        self.save_image_only = False

        # UI 更新
        if self.save_all:
            dpg.set_item_label(this_btn, "ON")
            dpg.bind_item_theme(this_btn, "theme_button_on")   # ★ 追加
        else:
            dpg.set_item_label(this_btn, "OFF")
            dpg.bind_item_theme(this_btn, "theme_button_off")  # ★ 追加

        # ★ AppFlags に反映
        self.config.app_flags = AppFlags(
            shutdown=self.config.app_flags.shutdown,
            pause=self.config.app_flags.pause,
            display_enabled=self.config.app_flags.display_enabled,
            save_mode="image_and_result" if self.save_all else "none",
        )


    def on_toggle_highlight(self, btn_tag: str) -> None:
        current = self.config.app_flags.highlight_enabled
        new_state = not current

        # UI 更新
        if new_state:
            dpg.set_item_label(btn_tag, "ON")
            dpg.bind_item_theme(btn_tag, "theme_button_on")    # ★ 追加
        else:
            dpg.set_item_label(btn_tag, "OFF")
            dpg.bind_item_theme(btn_tag, "theme_button_off")   # ★ 追加

        # AppFlags 更新
        self.config.app_flags = AppFlags(
            shutdown=self.config.app_flags.shutdown,
            pause=self.config.app_flags.pause,
            display_enabled=self.config.app_flags.display_enabled,
            save_mode=self.config.app_flags.save_mode,
            highlight_enabled=new_state,
        )

    def on_toggle_graph_display(self, btn_tag: str) -> None:
        current = self.config.app_flags.graph_enabled
        new_state = not current

        # UI 更新
        if new_state:
            dpg.set_item_label(btn_tag, "ON")
            dpg.bind_item_theme(btn_tag, "theme_button_on")
        else:
            dpg.set_item_label(btn_tag, "OFF")
            dpg.bind_item_theme(btn_tag, "theme_button_off")

        # AppFlags 更新（既存の値を維持しつつ graph_enabled だけ変更）
        self.config.app_flags = AppFlags(
            shutdown=self.config.app_flags.shutdown,
            pause=self.config.app_flags.pause,
            display_enabled=self.config.app_flags.display_enabled,
            save_mode=self.config.app_flags.save_mode,
            highlight_enabled=self.config.app_flags.highlight_enabled,
            graph_enabled=new_state,   # ★ ここだけ変更
        )



    # ---------------------------------------------------------
    # 記録開始・停止（まだ何もしない）
    # ---------------------------------------------------------
    def on_start_recording(self) -> None:
        """記録開始（まだ何もしない）"""
        pass

    def on_stop_recording(self) -> None:
        """記録停止（まだ何もしない）"""
        pass

    # ---------------------------------------------------------
    # LED 操作（まだ何もしない）
    # ---------------------------------------------------------
    def on_led_on(self) -> None:
        """LED ON（まだ何もしない）"""
        pass

    def on_led_off(self) -> None:
        """LED OFF（まだ何もしない）"""
        pass

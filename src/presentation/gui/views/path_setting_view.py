# src/presentation/gui/views/path_setting_view.py

from __future__ import annotations
import dearpygui.dearpygui as dpg

from presentation.gui.controllers.path_setting_controller import PathSettingController


class PathSettingView:
    """
    保存先フォルダや設定フォルダを指定する画面。
    UI の見た目だけを担当し、処理は PathSettingController に委譲する。
    """

    def __init__(self, controller: PathSettingController) -> None:
        self.controller = controller

        # UI 要素のタグ
        self.save_dir_input = "save_directory_input"
        self.config_dir_input = "config_directory_input"

    def render(self) -> None:
        """Path Setting タブの UI を描画する"""

        dpg.add_text("Path Setting")

        # --- 保存先フォルダ ---
        dpg.add_text("Save Directory")
        dpg.add_input_text(
            tag=self.save_dir_input,
            default_value="",
            width=400,
        )

        # --- 設定ファイルフォルダ ---
        dpg.add_text("Config Directory")
        dpg.add_input_text(
            tag=self.config_dir_input,
            default_value="",
            width=400,
        )

        dpg.add_separator()

        # --- 設定適用ボタン ---
        dpg.add_button(
            label="Apply Path Settings",
            width=200,
            callback=lambda: self.controller.on_apply_paths(
                save_dir=dpg.get_value(self.save_dir_input),
                config_dir=dpg.get_value(self.config_dir_input),
            )
        )

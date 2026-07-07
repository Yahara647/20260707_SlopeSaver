# src/presentation/gui/views/record_view.py

from __future__ import annotations
import dearpygui.dearpygui as dpg

from presentation.gui.controllers.record_controller import RecordController


class RecordView:
    """
    記録（保存開始/停止、LED 点灯/消灯など）を行うメイン画面。
    UI の見た目だけを担当し、処理は RecordController に委譲する。
    """

    def __init__(self, controller: RecordController) -> None:
        self.controller = controller

        # ボタンのタグ
        self.save_image_btn = "save_image_button"
        self.save_all_btn = "save_all_button"

    def render(self) -> None:
        """Record タブの UI を描画する"""

        dpg.add_text("【計測】")
        dpg.add_text("　・第一ボタン押下で計測を開始します")
        dpg.add_text("　　　- カメラ前に立つと20秒計測が停止します")
        dpg.add_spacer(height=5)
        dpg.add_text("　・第二ボタンで帯鋼歪み量が表示されます（開発中）")
        dpg.add_text("　　　- 最大歪み箇所に緑丸が表示されます")
        dpg.add_text("　　　- 左上に歪みの大きさが表示されます")
        dpg.add_spacer(height=5)
        dpg.add_separator()
        dpg.add_spacer(height=5)

        # # --- 保存モード切り替え（排他トグル） ---
        # dpg.add_button(
        #     label="Save Image Only (OFF)",
        #     tag=self.save_image_btn,
        #     width=250,
        #     callback=lambda: self.controller.on_toggle_save_image(self.save_image_btn, self.save_all_btn)
        # )
        dpg.add_text("　a. 計測")

        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_button(
                label="OFF",
                tag=self.save_all_btn,
                width=250,
                callback=lambda: self.controller.on_toggle_save_all(self.save_all_btn)
            )
            dpg.bind_item_theme(self.save_all_btn, "theme_button_off")

        dpg.add_spacer(height=10)
        dpg.add_separator()

        dpg.add_text("　b. 計測値表示（仮実装）")
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_button(
                label="OFF",
                tag="highlight_button",
                width=250,
                callback=lambda: self.controller.on_toggle_highlight("highlight_button")
            )
            dpg.bind_item_theme("highlight_button", "theme_button_off")

        dpg.add_spacer(height=10)
        dpg.add_separator()

        dpg.add_text("　c. グラフ表示（開発中）")
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_button(
                label="OFF",
                tag="graph_button",
                width=250,
                callback=lambda: self.controller.on_toggle_graph_display("graph_button")
            )
            dpg.bind_item_theme("graph_button", "theme_button_off")

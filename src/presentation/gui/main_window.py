# src/presentation/gui/main_window.py

from __future__ import annotations
import time
import dearpygui.dearpygui as dpg

from domain.aggregates.app_config import AppConfig
from domain.aggregates.calibration_preparation_result import CalibrationPreparationResult
from infrastructure.camera.pylon_camera_driver import PylonCameraDriver
from infrastructure.dio.dio_led_driver import DioLedDriver

from logger.logger import logger

from presentation.gui.views.record_view import RecordView
from presentation.gui.views.camera_setting_view import CameraSettingView
from presentation.gui.views.path_setting_view import PathSettingView

from presentation.gui.controllers.record_controller import RecordController
from presentation.gui.controllers.camera_setting_controller import CameraSettingController
from presentation.gui.controllers.path_setting_controller import PathSettingController


class MainWindow:

    def __init__(self, config: AppConfig, camera_service: PylonCameraDriver, dio_service: DioLedDriver, calibration_preparation_result: CalibrationPreparationResult) -> None:
        self.config = config
        self.camera_service = camera_service
        self.dio_service = dio_service
        self.calibration_preparation_result = calibration_preparation_result

        self.logger = logger
        self.logger.info("MainWindow initialized.")

        self.record_controller = RecordController(config, camera_service, dio_service)
        self.camera_setting_controller = CameraSettingController(config, camera_service, dio_service, calibration_preparation_result)
        self.path_setting_controller = PathSettingController(config, camera_service, dio_service)

        self.record_view = RecordView(self.record_controller)
        self.camera_setting_view = CameraSettingView(self.camera_setting_controller)
        self.path_setting_view = PathSettingView(self.path_setting_controller)

        # ★ GUI が閉じたかどうか
        self._closed = False

    def setup(self) -> None:
        self.logger.info("Setting up GUI...")

        dpg.create_context()

        # -------------------------------
        # ★ 日本語フォントの読み込み
        # -------------------------------
        with dpg.font_registry():
            self.jp_font = dpg.add_font(r"src\fonts\NotoSansJP-Regular.ttf", 18)

        dpg.create_viewport(title="Slope Saver", width=400, height=600)
        dpg.setup_dearpygui()

        # ★ フォントをデフォルトに設定
        dpg.bind_font(self.jp_font)

        with dpg.theme(tag="theme_button_on"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 180, 0))        # 緑
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 200, 0))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 150, 0))

        with dpg.theme(tag="theme_button_off"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (100, 100, 100))    # グレー
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (120, 120, 120))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (80, 80, 80))

        with dpg.window(label="MainWindow", tag="MainWindow", width=400, height=600, no_title_bar=True, no_move=True):

            with dpg.tab_bar():

                # --- Camera Setting タブ ---
                with dpg.tab(label="1. 設定", tag="tab_camera_setting"):
                    self.camera_setting_view.render()

                # --- Record タブ ---
                with dpg.tab(label="2. 計測", tag="tab_record"):
                    self.record_view.render()

                # # --- Path Setting タブ ---
                # with dpg.tab(label="Path Setting", tag="tab_path_setting"):
                #     self.path_setting_view.render()

        dpg.show_viewport()
        self.logger.info("GUI setup completed.")


    def run(self) -> None:
        self.logger.info("GUI starting...")
        self.setup()
        dpg.start_dearpygui()
        dpg.destroy_context()

        self._closed = True
        self.logger.info("GUI closed.")




    # ★ メインスレッドが GUI の終了を待つためのメソッド
    def wait_for_close(self) -> None:
        while not self._closed:
            time.sleep(0.05)


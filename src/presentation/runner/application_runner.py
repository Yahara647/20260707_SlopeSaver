# src/presentation/application_runner.py

from __future__ import annotations

from logging import Logger

from logger.logger import logger

from domain.aggregates.app_config import AppConfig
from domain.value_objects.config_values.app_flags import AppFlags
from domain.aggregates.calibration_preparation_result import CalibrationPreparationResult

from application.repositories.app_config_repository import AppConfigRepository
from application.repositories.calibration_preparation_result_repository import CalibrationPreparationResultRepository

from application.usecases.initialize_app_config_usecase import InitializeAppConfigUseCase
from application.usecases.high_exposure_capture_usecase import HighExposureCaptureUseCase
from application.usecases.full_reflection_measurement_usecase import FullReflectionMeasurementUseCase
from application.usecases.save_picture_usecase import SavePictureUseCase

from application.buffers.frame_buffer import FrameBuffer

from infrastructure.camera.pylon_camera_driver import PylonCameraDriver
from infrastructure.camera.camera_state import CameraState
from infrastructure.dio.dio_led_driver import DioLedDriver
from infrastructure.dio.dio_state import DioState

from presentation.gui.main_window import MainWindow
from presentation.threads.high_exposure_thread import HighExposureThread
from presentation.threads.display_thread import DisplayThread
from presentation.threads.low_exposure_compute_thread import LowExposureComputeThread


class ApplicationRunner:
    """
    アプリ全体の依存関係を構築し、
    UseCase / Infra / GUI / Thread を組み立てて起動する Composition Root。
    """

    def __init__(self) -> None:
        self.logger: Logger = logger

        # Aggregates
        self.config: AppConfig | None = None
        self.calibration_preparation_result: CalibrationPreparationResult | None = None

        # Infra
        self.camera_service: PylonCameraDriver | None = None
        self.dio_service: DioLedDriver | None = None

        # Application
        self.frame_buffer: FrameBuffer | None = None
        self.high_exposure_usecase: HighExposureCaptureUseCase | None = None
        self.full_measurement_usecase: FullReflectionMeasurementUseCase | None = None
        self.save_picture_usecase: SavePictureUseCase | None = None

        # Presentation
        self.gui: MainWindow | None = None
        self.high_exposure_thread: HighExposureThread | None = None
        self.display_thread: DisplayThread | None = None
        self.low_exposure_thread: LowExposureComputeThread | None = None

    # -----------------------------
    # 初期化フェーズ
    # -----------------------------

    def initialize_config(self) -> None:
        self.logger.info("Loading configuration...")

        # AppConfig
        app_repo = AppConfigRepository("config/last_app_config.json")
        usecase = InitializeAppConfigUseCase(app_repo)
        self.config = usecase.execute()

        # CalibrationPreparationResult
        calib_repo = CalibrationPreparationResultRepository("config/last_calibration_preparation.json")
        self.calibration_preparation_result = calib_repo.load()

        # ★ 起動時は必ず shutdown=False にリセットする
        assert self.config is not None
        old_flags = self.config.app_flags
        self.config.app_flags = AppFlags(
            shutdown=False,
            pause=old_flags.pause,
            display_enabled=old_flags.display_enabled,
            save_mode="none",
        )

        self.logger.info("Configuration loaded.")

    def initialize_services(self) -> None:
        assert self.config is not None
        assert self.calibration_preparation_result is not None

        self.logger.info("Initializing services...")

        # Camera
        self.camera_state = CameraState()
        self.camera_service = PylonCameraDriver(self.camera_state)
        self.camera_service.initialize()

        self.apply_app_config_to_camera()

        # DIO
        self.dio_state = DioState()
        self.dio_service = DioLedDriver(self.dio_state)
        self.dio_service.initialize()

        # Shared Buffer
        self.frame_buffer = FrameBuffer()

        # High Exposure Capture UseCase
        self.high_exposure_usecase = HighExposureCaptureUseCase(
            camera=self.camera_service,
            buffer=self.frame_buffer,
            app_config=self.config,   # ★ AppConfig を渡す
        )

        # FullReflectionMeasurementUseCase（低露光計測）
        self.full_measurement_usecase = FullReflectionMeasurementUseCase(
            camera_service=self.camera_service,
            led_driver=self.dio_service,
        )

        # SavePictureUseCase（画像保存）
        self.save_picture_usecase = SavePictureUseCase(
            camera_service=self.camera_service
        )

        self.logger.info("Services initialized.")

    def initialize_gui(self) -> None:
        assert self.config is not None
        assert self.camera_service is not None

        self.logger.info("Initializing GUI...")
        self.gui = MainWindow(self.config, self.camera_service, self.dio_service, self.calibration_preparation_result)
        self.logger.info("GUI initialized.")

    def initialize_threads(self) -> None:
        assert self.high_exposure_usecase is not None
        assert self.frame_buffer is not None
        assert self.config is not None
        assert self.calibration_preparation_result is not None
        assert self.full_measurement_usecase is not None
        assert self.save_picture_usecase is not None

        self.logger.info("Initializing threads...")

        # 高露光撮像スレッド
        self.high_exposure_thread = HighExposureThread(
            usecase=self.high_exposure_usecase
        )

        # 低露光計測スレッド
        self.low_exposure_thread = LowExposureComputeThread(
            usecase=self.full_measurement_usecase,
            save_picture_usecase=self.save_picture_usecase,
            app_config=self.config,
            calibration_preparation_result=self.calibration_preparation_result,
        )

        # 表示スレッド
        self.display_thread = DisplayThread(
            buffer=self.frame_buffer,
            app_config=self.config,
            window_name="LiveView",
        )

        self.logger.info("Threads initialized.")

    # -----------------------------
    # 起動
    # -----------------------------
    def start(self) -> None:
        assert self.gui is not None
        assert self.high_exposure_thread is not None
        assert self.display_thread is not None
        assert self.low_exposure_thread is not None

        self.logger.info("Starting high exposure capture thread...")
        self.high_exposure_thread.start()

        self.logger.info("Starting low exposure compute thread...")
        self.low_exposure_thread.start()

        self.logger.info("Starting display thread...")
        self.display_thread.start()

        self.logger.info("Starting GUI main loop...")
        self.gui.run()



    # -----------------------------
    # アプリ全体の起動
    # -----------------------------
    def run(self) -> None:
        self.logger.info("Application starting...")
        self.initialize_config()
        self.initialize_services()
        self.initialize_gui()
        self.initialize_threads()
        self.start()

        # GUI が閉じられるまでブロック
        self.logger.info("Waiting for GUI to close...")
        self.gui.wait_for_close()

        self.logger.info("Shutting down threads...")

        # --- ① 各スレッドに停止要求 ---
        if self.high_exposure_thread:
            self.high_exposure_thread.stop()

        if self.low_exposure_thread:
            self.low_exposure_thread.stop()

        if self.display_thread:
            self.display_thread.stop()

        # --- ② 完全停止を待つ ---
        if self.high_exposure_thread:
            self.high_exposure_thread.join()

        if self.low_exposure_thread:
            self.low_exposure_thread.join()

        if self.display_thread:
            self.display_thread.join()

        self.logger.info("All threads stopped.")

        # --- ③ 最後に LED 全消灯 ---
        try:
            assert self.full_measurement_usecase is not None
            self.logger.info("Turning off all LEDs via LedControlService...")
            self.full_measurement_usecase.compute_low_exposure_service.led_control_service.turn_off_all()
            self.logger.info("All LEDs turned OFF safely.")
        except Exception as e:
            self.logger.error(f"Failed to turn off LEDs: {e}")

        # --- 設定保存 ---
        self.logger.info("Saving last configuration...")
        try:
            assert self.config is not None
            app_repo = AppConfigRepository("config/last_app_config.json")
            app_repo.save(self.config)

            assert self.calibration_preparation_result is not None
            calib_repo = CalibrationPreparationResultRepository("config/last_calibration_preparation.json")
            calib_repo.save(self.calibration_preparation_result)

            self.logger.info("Configuration saved successfully.")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")

        self.logger.info("Application exited cleanly.")

    def apply_app_config_to_camera(self) -> None:
        cfg = self.config
        cam = self.camera_service

        # ROI
        cam.set_roi(
            x=cfg.led_reflection_area.x,
            y=cfg.led_reflection_area.y,
            w=cfg.led_reflection_area.width,
            h=cfg.led_reflection_area.height,
        )

        # 露光（表示用）
        cam.set_exposure_time(cfg.exposure_for_display.value)

from __future__ import annotations

import time
from threading import Thread
from typing import Optional
from pathlib import Path
import numpy as np

from logger.logger import logger
from domain.value_objects.config_values.app_flags import AppFlags
from domain.aggregates.app_config import AppConfig
from domain.aggregates.calibration_preparation_result import CalibrationPreparationResult
from domain.aggregates.projection_alignment_result import ProjectionAlignmentResult
from domain.aggregates.slope_computation_result import SlopeComputationResult
from domain.aggregates.measurement_evaluation_result import MeasurementEvaluationResult

from application.usecases.full_reflection_measurement_usecase import FullReflectionMeasurementUseCase
from application.usecases.save_measurement_results_usecase import SaveMeasurementResultsUseCase
from application.usecases.save_slit_measurement_results_usecase import SaveSlitMeasurementResultsUseCase
from application.usecases.save_measurement_evaluation_result_usecase import SaveMeasurementEvaluationResultUseCase
from application.usecases.compute_slit_measurement_evaluation_usecase import ComputeSlitMeasurementEvaluationUseCase
from application.usecases.save_picture_usecase import SavePictureUseCase
from application.usecases.compute_measurement_evaluation_usecase import ComputeMeasurementEvaluationUseCase
from application.usecases.compute_measurement_evaluation_from_led_world_usecase import ComputeMeasurementEvaluationFromLedWorldUseCase
from application.usecases.save_measurement_snapshot_line_usecase import SaveMeasurementSnapshotLineUseCase
from shared.shared_evaluation import shared_evaluation
from shared.shared_graph_data import shared_graph_data

# 新しいスリット光処理用サービス
from domain.services.led_position_detection_service import LedPositionDetectionService
from domain.services.led_frame_to_world_mapper_service import LedFrameToWorldMapperService
from domain.services.slit_light_detection_service import SlitLightDetectionService
from domain.services.slit_light_transformer_service import SlitLightTransformerService
from domain.services.slit_light_normal_calculator_service import SlitLightNormalCalculatorService
from domain.services.slit_light_slope_calculator_service import SlitLightSlopeCalculatorService
from domain.value_objects.computed_values.slit_light_points_in_frame import SlitLightPointsInFrame
from domain.value_objects.computed_values.slit_light_source_z_coords import SlitLightSourceZCoords

class LowExposureComputeThread:
    """
    スリット光源を用いた勾配計測を周期実行するスレッド。
    
    処理フロー:
    - ①②（10秒ごと）: LED位置検出・y-z マッピング生成
    - ③④⑤⑥（毎ループ）: スリット光検出→変換→法線→勾配計算
    """

    def __init__(
        self,
        usecase: FullReflectionMeasurementUseCase,
        save_picture_usecase: SavePictureUseCase,   # ★ DI で受け取る
        app_config: AppConfig,
        calibration_preparation_result: CalibrationPreparationResult,
        interval_sec: float = 1.0,
    ) -> None:

        self.usecase = usecase
        self.save_picture_usecase = save_picture_usecase  # ★ DI で保持
        self.app_config = app_config
        self.calibration_preparation_result = calibration_preparation_result
        self.interval_sec = interval_sec

        self._thread: Optional[Thread] = None
        self._logger = logger
        self._prev_save_mode = "none"

        # 結果保存 UseCase
        self.save_usecase = SaveMeasurementResultsUseCase()
        self.save_snapshot_line_usecase = SaveMeasurementSnapshotLineUseCase()
        self.save_slit_usecase = SaveSlitMeasurementResultsUseCase()
        self.save_evaluation_usecase = SaveMeasurementEvaluationResultUseCase()
        self.compute_slit_evaluation_usecase = ComputeSlitMeasurementEvaluationUseCase()

        # 10秒周期保存用
        self._last_picture_save_time = 0.0
        self._picture_save_interval = 10.0
        
        # スリット光処理用 - 新しいサービスを初期化
        self._led_position_detector = LedPositionDetectionService(
            led_control_service=self.usecase.compute_low_exposure_service.led_control_service,
            camera_capture_service=self.usecase.compute_low_exposure_service.camera_capture_service,
            app_config=self.app_config,
            logger=self._logger
        )
        self._led_frame_to_world_mapper = LedFrameToWorldMapperService(logger=self._logger)
        self._slit_light_detector = SlitLightDetectionService(logger=self._logger)
        self._slit_light_transformer = SlitLightTransformerService(logger=self._logger)
        self._slit_light_normal_calculator = SlitLightNormalCalculatorService(logger=self._logger)
        self._slit_light_slope_calculator = SlitLightSlopeCalculatorService(logger=self._logger)
        
        # LED位置検出用タイマー（5秒ごと）
        self._last_led_position_detection_time = 0.0
        self._led_position_detection_interval = 5.0
        
        # 前ループのLED検出結果・マッピング情報を保持
        self._prev_led_points_in_frame = None
        self._prev_led_numbers_in_frame = None
        self._led_y_to_z_mapping = None

    def start(self) -> None:
        if self._thread is not None:
            return

        self._logger.info("LowExposureComputeThread: start()")

        self._thread = Thread(
            target=self.run,
            daemon=True,
            name="LowExposureComputeThread",
        )
        self._thread.start()

    def run(self) -> None:
        self._logger.info("LowExposureComputeThread: run() started")

        while True:

            # シャットダウン
            if self.app_config.app_flags.shutdown:
                self._logger.info("LowExposureComputeThread: shutdown detected")
                break

            current_mode = self.app_config.app_flags.save_mode

            # Idle → Active の遷移で LED OFF
            if current_mode != "image_and_result" and self._prev_save_mode == "image_and_result":
                try:
                    self.usecase.compute_low_exposure_service.led_control_service.turn_off_all()
                except Exception as e:
                    self._logger.error(f"Failed to turn off LEDs in idle mode: {e}")

            # Idle のときはスキップ
            if current_mode != "image_and_result":
                self._prev_save_mode = current_mode
                time.sleep(0.1)
                continue

            # Active のときだけ計算
            start = time.time()

            # === 新しいシステムのみを実行 ===
            # ① ② 10秒ごと: LED位置検出と y-z マッピング生成
            now = time.time()
            if now - self._last_led_position_detection_time >= self._led_position_detection_interval:
                try:
                    self._logger.info("LED位置検出処理開始...")
                    
                    # LED位置検出（①）
                    success, led_frame_points, led_numbers = self._led_position_detector.detect_led_positions(
                        prev_detected_points=self._prev_led_points_in_frame,
                        prev_detected_led_numbers=self._prev_led_numbers_in_frame,
                        red_detector=self.usecase.compute_low_exposure_service.red_light_detection_service,
                    )
                    
                    if success:
                        self._prev_led_points_in_frame = led_frame_points
                        self._prev_led_numbers_in_frame = led_numbers
                        
                        # LED y-z マッピング生成（②）
                        # config から LED 世界座標を取得
                        led_world_coords = self.app_config.led_coordinates
                        if led_world_coords is not None and not led_world_coords.is_empty:
                            success_mapping, mapping_info = self._led_frame_to_world_mapper.create_mapping(
                                led_points_in_frame=led_frame_points,
                                led_world_coords=led_world_coords,
                            )
                            
                            if success_mapping:
                                self._led_y_to_z_mapping = mapping_info
                                self._logger.info("LED y-z マッピング生成成功")
                        
                        self._last_led_position_detection_time = now
                    else:
                        self._logger.warning("LED位置検出に失敗")
                        
                except Exception as e:
                    self._logger.exception(f"LED位置検出エラー: {e}")
            
            
            # ③ ④ ⑤ ⑥ 毎ループ: スリット光検出→変換→法線→勾配計算
            if self._led_y_to_z_mapping is not None:
                try:
                    self._logger.debug("スリット光処理開始...")
                    
                    # 現在のフレームを取得（スリット光検出用露光で撮像）
                    slit_exposure = self.app_config.exposure_for_slit_light.value
                    frame_for_slit = self.usecase.compute_low_exposure_service.camera_capture_service.capture_with_exposure(slit_exposure)
                    if frame_for_slit is None:
                        self._logger.warning("スリット光処理用フレーム取得失敗")
                    else:
                        # ③ スリット光検出
                        success_slit_detect, slit_points_frame, slit_source_z_coords = self._slit_light_detector.detect_slit_light(
                            frame=frame_for_slit.data if hasattr(frame_for_slit, 'data') else frame_for_slit,
                            app_config=self.app_config,
                            led_y_to_z_mapping=self._led_y_to_z_mapping,
                            led_frame_points=self._prev_led_points_in_frame,
                        )
                        
                        if success_slit_detect and slit_points_frame is not None:
                            # ④ スリット光ホモグラフィ変換
                            success_transform, slit_points_world = self._slit_light_transformer.transform_to_world(
                                slit_points_in_frame=slit_points_frame,
                                slit_source_z_coords=slit_source_z_coords,
                                homography_matrix=self.calibration_preparation_result.homography_matrix,
                                strip_z=self.app_config.strip_z.value,
                            )
                            
                            if success_transform and slit_points_world is not None:
                                # ⑤ スリット光法線計算
                                # スリット光源の3D座標を構築
                                slit_light_source_3d = self._construct_slit_light_source_coords(
                                    slit_points_frame, slit_source_z_coords
                                )
                                
                                if slit_light_source_3d is not None:
                                    success_normal, slit_normals = self._slit_light_normal_calculator.calculate(
                                        slit_light_source_in_world=slit_light_source_3d,
                                        slit_projection_in_world=slit_points_world,
                                        camera_coord=self.app_config.camera_coordinate,
                                    )
                                    
                                    if success_normal and slit_normals is not None:
                                        # ⑥ スリット光勾配計算
                                        success_slope, slit_slope_angles = self._slit_light_slope_calculator.calculate(
                                            normals=slit_normals
                                        )
                                        
                                        if success_slope and slit_slope_angles is not None:
                                            self._logger.debug(
                                                f"スリット光処理成功: "
                                                f"{len(slit_slope_angles.slopes_in_world)}個の勾配"
                                            )
                                            # 結果を SlopeComputationResult に集約して保存
                                            result = SlopeComputationResult(
                                                led_points_in_frame=self._prev_led_points_in_frame,
                                                led_numbers_in_frame=self._prev_led_numbers_in_frame,
                                                slit_points_in_frame=slit_points_frame,
                                                slit_source_z_coords=slit_source_z_coords,
                                                slit_points_in_world=slit_points_world,
                                                normal_vectors=slit_normals,
                                                slope_angles=slit_slope_angles,
                                            )
                                            out_dir = self.save_slit_usecase.execute(
                                                base_dir="output/results",
                                                app_config=self.app_config,
                                                calib=self.calibration_preparation_result,
                                                slope=result,
                                            )
                                            self._logger.info(f"スリット光計測結果を保存: {out_dir}")

                                            # スリット光計測結果から評価値を算出して保存
                                            evaluation = self.compute_slit_evaluation_usecase.execute(result)
                                            eval_out_dir = self.save_evaluation_usecase.execute(
                                                base_dir="output/evaluation_results",
                                                evaluation=evaluation,
                                            )
                                            self._logger.info(f"評価結果を保存: {eval_out_dir}")

                                            # 表示系 shared データを更新（横軸は slit_points_in_world の y 座標を使用）
                                            self._publish_display_data(result, evaluation)
                
                except Exception as e:
                    self._logger.exception(f"スリット光処理エラー: {e}")


            # ★ 10秒に1回だけ画像保存
            now = time.time()

            if now - self._last_picture_save_time >= self._picture_save_interval:
                try:
                    self.usecase.single_led_detection_service.led_control_service.turn_on_all()
                    pic_path = self.save_picture_usecase.execute(
                        base_dir="output/picture_low_exposure",
                        exposure=self.app_config.exposure_for_computation
                    )
                    # LED を全点灯状態に復旧（デフォルト状態を維持）
                    self.usecase.single_led_detection_service.led_control_service.turn_on_all()
                    if pic_path:
                        self._logger.info(f"Saved periodic picture: {pic_path}")
                    self._last_picture_save_time = now
                except Exception as e:
                    self._logger.error(f"Failed to save periodic picture: {e}")

            # ★ 高露光画像の 10 秒周期保存（既存保存の 5 秒後に実行）
            now = time.time()

            # 高露光保存の初回基準を作る（既存保存より 5 秒遅らせる）
            if not hasattr(self, "_last_low_exposure_save_time"):
                self._last_low_exposure_save_time = now - (self._picture_save_interval // 2)

            # 10 秒周期 + 5 秒遅延
            if now - self._last_low_exposure_save_time >= self._picture_save_interval:
                try:
                    low_pic_path = self.save_picture_usecase.execute(
                        base_dir="output/picture_high_exposure",
                        exposure=self.app_config.exposure_for_display
                    )
                    if low_pic_path:
                        self._logger.info(f"Saved low-exposure periodic picture: {low_pic_path}")

                    self._last_low_exposure_save_time = now

                except Exception as e:
                    self._logger.error(f"Failed to save low-exposure periodic picture: {e}")

            # 周期制御
            elapsed = time.time() - start
            sleep_time = self.interval_sec - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

            self._prev_save_mode = current_mode

        self._logger.info("LowExposureComputeThread: run() finished")

    def _construct_slit_light_source_coords(
        self,
        slit_points_frame: SlitLightPointsInFrame,
        slit_source_z_coords: SlitLightSourceZCoords,
    ) -> Optional[np.ndarray]:
        """
        スリット光源の3D座標を構築する。
        
        スリット光源は実空間の固定位置に存在し、
        x, y座標はAppConfigから、z座標はLED y-zマッピングから取得される。
        
        Parameters
        ----------
        slit_points_frame : SlitLightPointsInFrame
            スリット光の画像座標（使用されない）
        slit_source_z_coords : SlitLightSourceZCoords
            各スリット光検出点に対応するz座標
            
        Returns
        -------
        slit_light_source_3d : np.ndarray, optional
            スリット光源の実空間座標 (N, 3)
            または None（失敗時）
        """
        
        try:
            if slit_points_frame is None or slit_points_frame.is_empty:
                return None
            if slit_source_z_coords is None or slit_source_z_coords.is_empty:
                return None
            
            # AppConfigから固定座標を取得
            slit_x = self.app_config.slit_light_source_x_coordinate.value
            slit_y = self.app_config.slit_light_source_y_coordinate.value
            
            z_coords = slit_source_z_coords.values  # (N,)
            
            # スリット光源の3D座標を構築
            # x, y: AppConfigの固定値
            # z: LED y-zマッピングから取得
            slit_3d_coords = []
            for z_value in z_coords:
                slit_3d_coords.append([slit_x, slit_y, float(z_value)])
            
            slit_light_source_3d = np.array(slit_3d_coords, dtype=np.float64)
            
            return slit_light_source_3d
            
        except Exception as e:
            if self._logger:
                self._logger.exception(f"スリット光源3D座標構築エラー: {e}")
            return None

    def _publish_display_data(
        self,
        result: SlopeComputationResult,
        evaluation: MeasurementEvaluationResult,
    ) -> None:
        """表示スレッド向け共有データを更新する。"""
        try:
            score_index = int(evaluation.slope_distortion.slope_score_index)

            # b. 計測値表示向け
            highlight_point = None
            frame_points = result.slit_points_in_frame.coords_in_frame
            if frame_points is not None and 0 <= score_index < len(frame_points):
                px, py = frame_points[score_index]
                highlight_point = (int(px), int(py))

            with shared_evaluation.lock:
                shared_evaluation.slope_score = float(evaluation.slope_distortion.slope_score)
                shared_evaluation.slope_score_index = score_index
                shared_evaluation.highlight_point = highlight_point

            # c. グラフ表示向け
            # DisplayThread は red_in_world[:, 1] を横軸に使用するため、
            # slit_points_in_world をそのまま渡すと y 座標が横軸になる。
            world_points = result.slit_points_in_world.coords_in_world
            # 縦軸は一次残差そのものを使用する。
            residuals = evaluation.linear_residuals.residuals

            with shared_graph_data.lock:
                if (
                    world_points is not None
                    and residuals is not None
                    and len(world_points) == len(residuals)
                ):
                    shared_graph_data.red_in_world = world_points.copy()
                    shared_graph_data.slope_linear_residuals_min_adjusted = residuals.copy()
                else:
                    shared_graph_data.red_in_world = None
                    shared_graph_data.slope_linear_residuals_min_adjusted = None
                    self._logger.warning(
                        "表示用グラフデータの要素数が不一致のため更新をスキップしました"
                    )

        except Exception as e:
            self._logger.exception(f"表示用 shared データ更新エラー: {e}")

    def stop(self) -> None:
        self._logger.info("LowExposureComputeThread: stop()")
        self.app_config.app_flags = AppFlags(
            shutdown=True,
            pause=self.app_config.app_flags.pause,
            display_enabled=self.app_config.app_flags.display_enabled,
        )

    def join(self, timeout: float | None = None) -> None:
        if self._thread is not None:
            self._logger.info("LowExposureComputeThread: join()")
            self._thread.join(timeout)

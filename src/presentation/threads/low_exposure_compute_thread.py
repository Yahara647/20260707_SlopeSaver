from __future__ import annotations

import time
from threading import Thread
from typing import Optional
from pathlib import Path

from logger.logger import logger
from domain.value_objects.config_values.app_flags import AppFlags
from domain.aggregates.app_config import AppConfig
from domain.aggregates.calibration_preparation_result import CalibrationPreparationResult
from domain.aggregates.projection_alignment_result import ProjectionAlignmentResult
from domain.aggregates.slope_computation_result import SlopeComputationResult

from application.usecases.full_reflection_measurement_usecase import FullReflectionMeasurementUseCase
from application.usecases.save_measurement_results_usecase import SaveMeasurementResultsUseCase
from application.usecases.save_picture_usecase import SavePictureUseCase
from application.usecases.compute_measurement_evaluation_usecase import ComputeMeasurementEvaluationUseCase
from application.usecases.compute_measurement_evaluation_from_led_world_usecase import ComputeMeasurementEvaluationFromLedWorldUseCase
from application.usecases.save_measurement_snapshot_line_usecase import SaveMeasurementSnapshotLineUseCase
from shared.shared_evaluation import shared_evaluation
from shared.shared_graph_data import shared_graph_data

class LowExposureComputeThread:
    """
    LED1点位置検出 → 全LED点灯で勾配計算 を周期実行するスレッド。
    UseCase の orchestration のみを担当する。
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

        # 10秒周期保存用
        self._last_picture_save_time = 0.0
        self._picture_save_interval = 10.0

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

            try:
                (
                    success,
                    marker_led_coord_in_frame,
                    led_numbers,
                    red_in_frame,
                    red_in_world,
                    led_world_coords,
                    reflection_normals,
                    strip_slopes,
                    slope_angles,
                ) = self.usecase.run(
                    projection_alignment_led_number=self.app_config.projection_alignment_led_number,
                    exposure_for_computation=self.app_config.exposure_for_computation,
                    led_coordinates=self.app_config.led_coordinates,
                    camera_coordinate=self.app_config.camera_coordinate,
                    homography_matrix=self.calibration_preparation_result.homography_matrix,
                    strip_z=self.app_config.strip_z,
                )

                if not success:
                    continue

            except Exception as e:
                self._logger.error(f"LowExposureComputeThread: error: {e}")
                continue

            # アグリゲート生成
            calib_result = CalibrationPreparationResult(
                calibration_leds_in_frame=self.calibration_preparation_result.calibration_leds_in_frame,
                homography_matrix=self.calibration_preparation_result.homography_matrix,
            )

            proj_align_result = ProjectionAlignmentResult(
                single_bright_point_in_frame=marker_led_coord_in_frame
            )

            slope_result = SlopeComputationResult(
                slope_angles=slope_angles,
                red_bright_points_in_frame=red_in_frame,
                red_bright_points_in_world=red_in_world,
                led_numbers_in_frame=led_numbers,
                led_world_coordinates_in_frame=led_world_coords,
                normal_vectors=reflection_normals,
                strip_slopes=strip_slopes,
            )

            # 結果保存
            try:
                save_dir: Path = self.save_usecase.execute(
                    base_dir="output/results",
                    app_config=self.app_config,
                    calib=calib_result,
                    proj=proj_align_result,
                    slope=slope_result,
                )
                # self._logger.info(f"Saved measurement results to: {save_dir}")

            except Exception as e:
                self._logger.error(f"Failed to save measurement results: {e}")


            # 評価 UseCase を実行
            try:
                evaluation_usecase = ComputeMeasurementEvaluationUseCase()
                evaluation_result = evaluation_usecase.execute(slope_result)
                # evaluation_usecase = ComputeMeasurementEvaluationFromLedWorldUseCase()
                # evaluation_result = evaluation_usecase.execute(slope_result)

                # ★ 保存 UseCase を実行
                from application.usecases.save_measurement_evaluation_result_usecase import (
                    SaveMeasurementEvaluationResultUseCase,
                )

                save_eval_usecase = SaveMeasurementEvaluationResultUseCase()
                eval_save_dir = save_eval_usecase.execute(
                    base_dir="output/evaluation_results",
                    evaluation=evaluation_result,
                )

                snapshot_path = self.save_snapshot_line_usecase.execute(
                    base_dir="output/daily_snapshots",
                    app_config=self.app_config,
                    calib=calib_result,
                    proj=proj_align_result,
                    slope=slope_result,
                    evaluation=evaluation_result,
                )

                self._logger.info(f"Saved evaluation results to: {eval_save_dir}")
                self._logger.info(f"Appended daily snapshot line to: {snapshot_path}")

                with shared_evaluation.lock:
                    shared_evaluation.slope_score = evaluation_result.slope_distortion.slope_score
                    shared_evaluation.slope_score_index = evaluation_result.slope_distortion.slope_score_index

                    # # red_bright_points_in_frame から座標を取得 (20260116 ~14:07)
                    # idx = evaluation_result.slope_distortion.slope_score_index
                    # point = slope_result.red_bright_points_in_frame.coords_in_frame[idx]

                    # red_bright_points_in_frame から最大座標を取得 (20260116 14:07~)
                    coords = slope_result.red_bright_points_in_frame.coords_in_frame
                    idx = coords[:, 0].argmax()
                    point = coords[idx]


                    shared_evaluation.highlight_point = (int(point[0]), int(point[1]))

            except Exception as e:
                self._logger.error(f"Failed to evaluate measurement: {e}")


            try:
                with shared_graph_data.lock:
                    # 世界座標の赤輝点（ndarray）
                    shared_graph_data.red_in_world = slope_result.red_bright_points_in_world.coords_in_world

                    # 一次残差の最小値補正 residuals (ndarray)
                    shared_graph_data.slope_linear_residuals_min_adjusted = (
                        evaluation_result.linear_min_adjusted.residuals
                    )

            except Exception as e:
                self._logger.error(f"Failed to update shared graph data: {e}")




            # ★ 10秒に1回だけ画像保存
            now = time.time()

            if now - self._last_picture_save_time >= self._picture_save_interval:
                try:
                    self.usecase.single_led_detection_service.led_control_service.turn_on_all()
                    pic_path = self.save_picture_usecase.execute(
                        base_dir="output/picture_low_exposure",
                        exposure=self.app_config.exposure_for_computation
                    )
                    self.usecase.single_led_detection_service.led_control_service.turn_off_all()
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

"""
LED位置検出サービス

LEDを1つだけ点灯して撮像し、その投影位置をLED番号と対応付ける。
"""

from __future__ import annotations
from typing import Tuple, Optional
import time
import numpy as np
from logging import Logger

from domain.value_objects.config_values.projection_alignment_led_number import ProjectionAlignmentLedNumber
from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame
from domain.value_objects.computed_values.led_numbers_in_frame import LedNumbersInFrame
from domain.value_objects.computed_values.single_bright_point_in_frame import SingleBrightPointInFrame
from domain.aggregates.app_config import AppConfig
from domain.services.single_led_alignment_service import SingleLedAlignmentService
from application.services.led.led_control_service import LedControlService
from application.services.camera.camera_capture_service import CameraCaptureService


class LedPositionDetectionService:
    """
    LED位置検出サービス
    
    LEDを1つだけ点灯して撮像し、検出された点をそのLEDの投影位置として扱う。
    """
    
    def __init__(self, 
                 led_control_service: LedControlService,
                 camera_capture_service: CameraCaptureService,
                 app_config: AppConfig,
                 logger: Optional[Logger] = None) -> None:
        self.led_control_service = led_control_service
        self.camera_capture_service = camera_capture_service
        self.app_config = app_config
        self.logger = logger
        self.alignment_service = SingleLedAlignmentService(logger=logger)
    
    def detect_led_positions(
        self,
        prev_detected_points: Optional[RedBrightPointsInFrame],
        prev_detected_led_numbers: Optional['LedNumbersInFrame'],
        red_detector,  # 赤色点検出ロジック（既存）
    ) -> Tuple[bool, Optional[RedBrightPointsInFrame], Optional[LedNumbersInFrame]]:
        """
        LED位置を検出する。
        
        処理フロー:
        1. 前ループの検出LED番号から中央値を選ぶ（初回は LED 0）
        2. 選択したLEDだけを点灯して撮像
        3. 赤色点を1点検出し、そのLEDを基準点にする
        4. 全LEDを点灯して撮像し、基準点から各LED番号を割り当てる
        
        Parameters
        ----------
        prev_detected_points : RedBrightPointsInFrame, optional
            前ループで検出された赤色点
        prev_detected_led_numbers : LedNumbersInFrame, optional
            前ループで検出されたLED番号
        red_detector : object
            赤色点検出ロジック
            
        Returns
        -------
        (success, led_points_in_frame, led_numbers)
            success : bool
            led_points_in_frame : RedBrightPointsInFrame
                LED投影座標
            led_numbers : LedNumbersInFrame
                対応するLED番号
        """
        
        try:
            # --- ステップ1: 前ループから探索開始LED番号を決定 ---
            # 初回実行時は前フレームがないため、LED 0を点灯対象に設定
            if prev_detected_led_numbers is None or prev_detected_led_numbers.is_empty:
                start_led = 0
                if self.logger:
                    self.logger.info("初回実行: LED位置検出のため、デフォルトでLED 0を点灯対象に設定")
            else:
                # 前回検出されたLED番号の中央値を取得
                median_led_number = int(np.median(prev_detected_led_numbers.led_nums))
                start_led = median_led_number
                
                if self.logger:
                    self.logger.info(
                        f"LED位置検出: "
                        f"前フレームの検出LED番号={prev_detected_led_numbers.led_nums}, "
                        f"中央値LED番号={median_led_number}, "
                        f"探索開始LED={start_led}"
                    )
            
            # --- ステップ2: 対象LEDだけを点灯して撮像。失敗したら次のLEDへ進む ---
            num_leds = self.led_control_service.led_driver.state.output_num
            exposure = self.app_config.exposure_for_computation.value

            for attempt in range(num_leds):
                candidate_led = (start_led + attempt) % num_leds

                if self.logger:
                    self.logger.info(
                        f"LED位置検出: LED {candidate_led} を単一点灯して試行 ({attempt + 1}/{num_leds})"
                    )

                if not self.led_control_service.turn_only(candidate_led):
                    if self.logger:
                        self.logger.warning(f"LED {candidate_led} の単一点灯に失敗。次の候補へ")
                    continue

                time.sleep(0.1)
                frame_single_on = self.camera_capture_service.capture_with_exposure(exposure)

                # 単LED撮像後はLEDを消灯する
                self.led_control_service.turn_off_all()

                if frame_single_on is None:
                    if self.logger:
                        self.logger.warning(f"LED {candidate_led} 単一点灯時の撮像に失敗。次の候補へ")
                    continue

                detected_points = red_detector.detect(frame_single_on)
                if detected_points is None or detected_points.is_empty:
                    if self.logger:
                        self.logger.warning(f"LED {candidate_led} 単一点灯時に赤色点が見つかりません。次の候補へ")
                    continue

                coords = detected_points.coords_in_frame
                if len(coords) != 1:
                    if self.logger:
                        self.logger.warning(
                            f"LED {candidate_led} 単一点灯時の検出点数が1点ではありません: {len(coords)}点。次の候補へ"
                        )
                    continue

                single_point = coords.astype(np.int32).reshape(1, 2)
                marker_point = SingleBrightPointInFrame.create(single_point)
                marker_led = ProjectionAlignmentLedNumber.create(candidate_led)
                
                if not marker_point or not marker_led:
                    if self.logger:
                        self.logger.error("単LED基準点またはLED番号の生成に失敗")
                    return False, None, None

                # 全LED撮像の直前だけ全点灯する
                self.led_control_service.turn_on_all()
                time.sleep(0.1)
                frame_all_on = self.camera_capture_service.capture_with_exposure(exposure)

                # 全LED撮像後はすぐに消灯し、以降の画像処理中は点灯させない
                self.led_control_service.turn_off_all()

                if frame_all_on is None:
                    if self.logger:
                        self.logger.warning(f"LED {candidate_led} 基準での全LED点灯撮像に失敗。次の候補へ")
                    continue

                detected_all_points = red_detector.detect(frame_all_on)
                if detected_all_points is None or detected_all_points.is_empty:
                    if self.logger:
                        self.logger.warning(f"LED {candidate_led} 基準での全LED点検出に失敗。次の候補へ")
                    continue

                success_align, led_numbers, led_points = self.alignment_service.assign(
                    marker_led_num=marker_led,
                    marker_led_coord=marker_point,
                    detected_coords=detected_all_points,
                )

                if not success_align or led_numbers is None or led_points is None:
                    if self.logger:
                        self.logger.warning(f"LED {candidate_led} 基準でのLED番号割当に失敗。次の候補へ")
                    continue

                if self.logger:
                    x, y = single_point[0]
                    self.logger.info(
                        f"LED位置検出成功: 基準LED {candidate_led} の投影位置=({int(x)}, {int(y)}), "
                        f"検出LED番号={led_numbers.led_nums.tolist()}"
                    )
                
                return True, led_points, led_numbers

            self.led_control_service.turn_off_all()
            if self.logger:
                self.logger.error("全LEDを試しましたが、単一点灯で投影位置を検出できませんでした")
            return False, None, None
            
        except Exception as e:
            if self.logger:
                self.logger.exception(f"LED位置検出エラー: {e}")
            return False, None, None
    
    def _find_disappeared_point(
        self,
        points_all_on: RedBrightPointsInFrame,
        points_one_off: RedBrightPointsInFrame,
        distance_threshold: float = 10.0
    ) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """
        全点灯時と1点消灯時の差分から、消えた点を検出する。
        
        Returns
        -------
        (disappeared_point, disappear_idx)
            disappeared_point: 消えた点の座標 (x, y)
            disappear_idx: 全点灯時でのインデックス
        """
        
        all_on_coords = points_all_on.coords_in_frame
        one_off_coords = points_one_off.coords_in_frame
        
        if all_on_coords is None or one_off_coords is None:
            return None, None
        
        # 全点灯時の各点について、消灯後に存在するか確認
        for idx, point_on in enumerate(all_on_coords):
            found = False
            for point_off in one_off_coords:
                dist = np.linalg.norm(point_on - point_off)
                if dist < distance_threshold:
                    found = True
                    break
            
            if not found:
                # この点が消えた
                return point_on, idx
        
        return None, None
    
    def _assign_led_numbers(
        self,
        points_all_on: RedBrightPointsInFrame,
        disappear_idx: int,
        led_that_turned_off: int,
        total_leds: int,
    ) -> Tuple[Optional[LedNumbersInFrame], Optional[np.ndarray]]:
        """
        消えた点のインデックスとその実際のハードウェアLED番号から、
        全検出点のLED番号を対応付ける。
        
        仮定:
        - 点はy座標順にLEDが連番で並んでいる
        - disappear_idx の点が led_that_turned_off 番のLEDに対応する
        
        Returns
        -------
        (led_numbers, sorted_points)
            led_numbers: LedNumbersInFrame
            sorted_points: y座標でソートされた点の座標
        """
        
        coords = points_all_on.coords_in_frame
        if coords is None:
            return None, None
        
        # y座標でソート
        sorted_indices = np.argsort(coords[:, 1])
        sorted_points = coords[sorted_indices]
        
        # ソート後の配列での消えた点の位置を特定
        sorted_positions = np.where(sorted_indices == disappear_idx)[0]
        if len(sorted_positions) == 0:
            if self.logger:
                self.logger.error(
                    f"disappear_idx={disappear_idx} がソート後に見つかりません"
                )
            return None, None
        sorted_disappear_pos = int(sorted_positions[0])
        
        # ハードウェアLED番号を割り当て:
        # sorted_disappear_pos 番目の点 = led_that_turned_off 番のLED
        # → 各位置の番号 = led_that_turned_off + (i - sorted_disappear_pos)
        num_visible = len(sorted_points)
        led_numbers_arr = np.array(
            [led_that_turned_off + (i - sorted_disappear_pos) for i in range(num_visible)],
            dtype=np.int32,
        )
        
        # 有効範囲 [0, total_leds-1] にクランプ
        led_numbers_arr = np.clip(led_numbers_arr, 0, total_leds - 1)
        
        if self.logger:
            self.logger.info(
                f"LED番号割り当て: sorted_disappear_pos={sorted_disappear_pos}, "
                f"led_that_turned_off={led_that_turned_off}, "
                f"割り当て番号={led_numbers_arr.tolist()}"
            )
        
        led_numbers = LedNumbersInFrame.create(led_numbers_arr)
        if not led_numbers:
            return None, None
        
        return led_numbers, sorted_points

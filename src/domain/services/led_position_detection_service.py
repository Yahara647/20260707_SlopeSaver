"""
LED位置検出サービス

点光源がすべて点灯された状態で撮像し、その後一つを消灯して撮像。
消灯前後で消えた点を検出し、LED番号と画像座標を対応付ける。
"""

from __future__ import annotations
from typing import Tuple, Optional
import numpy as np
from logging import Logger

from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame
from domain.value_objects.computed_values.led_numbers_in_frame import LedNumbersInFrame
from domain.aggregates.app_config import AppConfig
from application.services.led.led_control_service import LedControlService
from application.services.camera.camera_capture_service import CameraCaptureService


class LedPositionDetectionService:
    """
    LED位置検出サービス
    
    全LED点灯時と1つ消灯時の2枚の画像を比較して、
    消えた点を検出し、LED番号と画像座標を対応付ける。
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
        2. 全LED点灯で撮像 → 赤色点検出
        3. 選択したLEDを消灯して撮像 → 赤色点検出
        4. 差分から消えた点を特定 → LED番号と対応付け
        5. その他のLED番号は位置関係から推定
        
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
            # --- ステップ1: 前ループから消灯対象のLED番号を決定 ---
            # 初回実行時は前フレームがないため、LED 0を消灯対象に設定
            if prev_detected_led_numbers is None or prev_detected_led_numbers.is_empty:
                led_to_turn_off = 0  # デフォルト：最初のLED（番号0）を消灯
                if self.logger:
                    self.logger.info("初回実行: LED位置検出のため、デフォルトでLED 0を消灯対象に設定")
            else:
                # 前回検出されたLED番号の中央値を取得
                median_led_number = int(np.median(prev_detected_led_numbers.led_nums))
                led_to_turn_off = median_led_number
                
                if self.logger:
                    self.logger.info(
                        f"LED位置検出: "
                        f"前フレームの検出LED番号={prev_detected_led_numbers.led_nums}, "
                        f"中央値LED番号={median_led_number}, "
                        f"消灯予定LED={led_to_turn_off}"
                    )
            
            # --- ステップ①: 全LED点灯で撮像 ---
            self.led_control_service.turn_on_all()
            # 短い安定化待機時間
            import time
            time.sleep(0.1)
            
            frame_all_on = self.camera_capture_service.capture_with_exposure(self.app_config.exposure_for_computation.value)
            if frame_all_on is None:
                if self.logger:
                    self.logger.error("全LED点灯時の撮像に失敗")
                return False, None, None
            
            # 赤色点検出
            result_all_on = red_detector.detect(frame_all_on)
            if not result_all_on:
                if self.logger:
                    self.logger.error("全LED点灯時の赤色点検出に失敗")
                return False, None, None
            
            red_points_all_on = result_all_on  # RedBrightPointsInFrame
            
            # --- ステップ②: 消灯候補を順番にずらして消失点を探す ---
            num_leds = self.led_control_service.led_driver.state.output_num
            exposure = self.app_config.exposure_for_computation.value
            
            disappeared_point = None
            disappear_idx = None
            led_that_turned_off = None
            
            for attempt in range(num_leds):
                candidate_led = (led_to_turn_off + attempt) % num_leds
                
                if self.logger:
                    self.logger.info(f"消失点探索: LED {candidate_led} を消灯して試行 ({attempt + 1}/{num_leds})")
                
                # 候補LEDを消灯して撮像
                self.led_control_service.turn_off_only(candidate_led)
                time.sleep(0.1)
                
                frame_one_off = self.camera_capture_service.capture_with_exposure(exposure)
                
                # 撮像後は全LED再点灯（次の試行のため）
                self.led_control_service.turn_on_all()
                
                if frame_one_off is None:
                    if self.logger:
                        self.logger.warning(f"LED {candidate_led} 消灯時の撮像に失敗。スキップ")
                    continue
                
                result_one_off = red_detector.detect(frame_one_off)
                if not result_one_off:
                    if self.logger:
                        self.logger.warning(f"LED {candidate_led} 消灯時の赤色点検出に失敗。スキップ")
                    continue
                
                # 差分から消えた点を特定
                candidate_disappeared, candidate_idx = self._find_disappeared_point(
                    red_points_all_on,
                    result_one_off
                )
                
                if candidate_disappeared is not None:
                    disappeared_point = candidate_disappeared
                    disappear_idx = candidate_idx
                    led_that_turned_off = candidate_led
                    if self.logger:
                        self.logger.info(
                            f"消失点発見: LED {candidate_led} 消灯により点(index={candidate_idx})が消失"
                        )
                    break
                else:
                    if self.logger:
                        self.logger.warning(
                            f"LED {candidate_led} 消灯では消失点が見つかりません。次の候補へ"
                        )
            
            if disappeared_point is None:
                if self.logger:
                    self.logger.error("全LEDを試しましたが消えた点が見つかりません")
                return False, None, None
            
            # --- ステップ5: LED番号を対応付け ---
            led_numbers, sorted_points = self._assign_led_numbers(
                red_points_all_on,
                disappear_idx,
                led_that_turned_off,
                num_leds
            )
            
            if led_numbers is None:
                if self.logger:
                    self.logger.error("LED番号の対応付けに失敗")
                return False, None, None
            
            # RedBrightPointsInFrameを再構築
            led_points = RedBrightPointsInFrame.create(sorted_points)
            if not led_points:
                if self.logger:
                    self.logger.error("LED点座標の生成に失敗")
                return False, None, None
            
            if self.logger:
                self.logger.info(
                    f"LED位置検出成功: {len(sorted_points)}個のLED位置を検出"
                )
            
            return True, led_points, led_numbers
            
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

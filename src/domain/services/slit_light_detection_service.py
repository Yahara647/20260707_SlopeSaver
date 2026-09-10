"""
スリット光検出サービス

画像上のスリット光点を検出し、LED y-z マッピングから光源z座標を対応付ける。
スリット光は縦に線が並んでいる状態を想定。

検出アルゴリズム:
  1. 赤色の点光源領域を輝度0にマスクする
  2. Bチャンネルの輝度閾値で二値化する
  3. 各y座標について明部分の重心x座標を求める
  4. 点群 (x, y) を出力し、LED y-z マッピングからz座標を付与する
"""

from __future__ import annotations
from typing import Tuple, Optional
import cv2
import numpy as np
from logging import Logger

from domain.value_objects.computed_values.slit_light_points_in_frame import SlitLightPointsInFrame
from domain.value_objects.computed_values.slit_light_source_z_coords import SlitLightSourceZCoords
from domain.aggregates.app_config import AppConfig


class SlitLightDetectionService:
    """
    スリット光検出サービス
    
    画像からスリット光の点群を検出し、
    LED y-z マッピングから対応する光源z座標を取得する。
    """
    
    def __init__(
        self,
        red_r_threshold: int = 100,
        red_diff_threshold: int = 50,
        blue_threshold: int = 30,
        min_bright_pixels: int = 3,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        Parameters
        ----------
        red_r_threshold : int
            赤色判定の R チャンネル最小値（BGR画像）
        red_diff_threshold : int
            赤色判定の R-G / R-B の最小差分
        blue_threshold : int
            スリット光判定の B チャンネル最小値
        min_bright_pixels : int
            1行あたりの最小輝点数（これ未満の行は外乱とみなしスキップ）
        """
        self.red_r_threshold = red_r_threshold
        self.red_diff_threshold = red_diff_threshold
        self.blue_threshold = blue_threshold
        self.min_bright_pixels = min_bright_pixels
        self.logger = logger
    
    def detect_slit_light(
        self,
        frame: np.ndarray,
        app_config: AppConfig,
        led_y_to_z_mapping: dict,
        led_frame_points=None,   # RedBrightPointsInFrame: LED投影位置（y範囲フィルタ用）
        slit_light_detector=None,  # 互換性のため残す（未使用）
    ) -> Tuple[bool, Optional[SlitLightPointsInFrame], Optional[SlitLightSourceZCoords]]:
        """
        スリット光を検出し、光源z座標を対応付ける。
        
        Parameters
        ----------
        frame : np.ndarray
            撮像された画像フレーム（BGR, uint8）
        app_config : AppConfig
            設定
        led_y_to_z_mapping : dict
            LED y-z マッピング情報
        led_frame_points : RedBrightPointsInFrame, optional
            検出済みのLED投影座標。指定時はLEDの配置間隔に基づいて
            範囲外のスリット光点を除去する。
        slit_light_detector : (未使用)
            互換性のために残す
            
        Returns
        -------
        (success, slit_light_points)
            success : bool
            slit_light_points : SlitLightPointsInFrame
        """
        
        try:
            if frame is None:
                if self.logger:
                    self.logger.error("フレームが None です")
                return False, None, None

            # --- モノクロカメラ対応: RGB/BGR の前提を取り除く ---
            if isinstance(frame, np.ndarray) and frame.ndim == 3 and frame.shape[2] == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            elif isinstance(frame, np.ndarray) and frame.ndim == 2:
                gray = frame
            else:
                if self.logger:
                    self.logger.error("スリット光検出には 2D グレースケール画像が必要です")
                return False, None, None

            # --- ステップ1: 輝度閾値でマスク ---
            frame_masked = self._mask_red_area(gray)
            # --- ステップ2: 明度閾値で二値化 ---
            binary = (frame_masked.astype(np.int16) >= self.blue_threshold)
            
            # --- ステップ3: 各 y 行について輝点の重心 x を求める ---
            slit_coords = self._extract_center_per_row(binary, gray)
            
            if len(slit_coords) == 0:
                if self.logger:
                    self.logger.warning("スリット光が検出されませんでした")
                return False, None, None
            
            slit_coords_arr = np.array(slit_coords, dtype=np.int32)  # shape (N, 2): (x, y)
            
            # --- ステップ3.5: LED y座標範囲によるフィルタ ---
            slit_coords_arr = self._filter_by_led_y_range(slit_coords_arr, led_frame_points)
            
            if len(slit_coords_arr) == 0:
                if self.logger:
                    self.logger.warning("LED y範囲フィルタ後にスリット光点がありません")
                return False, None, None
            
            if self.logger:
                self.logger.debug(
                    f"スリット光輝点検出: {len(slit_coords_arr)}点"
                )
            
            # --- ステップ4: LED y-z マッピングから各点の z 座標を付与 ---
            z_coords = []
            valid_coords = []
            
            for x, y in slit_coords_arr:
                z_value = self._get_z_from_mapping(float(y), led_y_to_z_mapping)
                if z_value is not None:
                    valid_coords.append((x, y))
                    z_coords.append(z_value)
            
            if len(valid_coords) == 0:
                if self.logger:
                    self.logger.warning("z座標マッピング後に有効な点がありません")
                return False, None, None
            
            valid_coords_arr = np.array(valid_coords, dtype=np.int32)
            z_coords_arr = np.array(z_coords, dtype=np.float32)
            
            slit_points_obj = SlitLightPointsInFrame.create(valid_coords_arr)
            if not slit_points_obj:
                if self.logger:
                    self.logger.error("SlitLightPointsInFrame の生成に失敗")
                return False, None, None
            
            slit_source_z_obj = SlitLightSourceZCoords.create(z_coords_arr)
            if not slit_source_z_obj:
                if self.logger:
                    self.logger.error("SlitLightSourceZCoords の生成に失敗")
                return False, None, None
            
            if self.logger:
                self.logger.info(
                    f"スリット光検出成功: {len(valid_coords_arr)}点"
                )
            
            return True, slit_points_obj, slit_source_z_obj
            
        except Exception as e:
            if self.logger:
                self.logger.exception(f"スリット光検出エラー: {e}")
            return False, None, None
    
    # ------------------------------------------------------------------
    # 内部メソッド
    # ------------------------------------------------------------------
    
    def _mask_red_area(self, frame: np.ndarray) -> np.ndarray:
        """
        色情報を前提にしないモノクロ対応版。
        画素値が閾値を超える領域を 0 にして、明るい領域だけを残す形にする。
        旧来の RGB 赤判定ロジックはモノクロカメラでは意味を持たないため、
        輝度閾値ベースで動作させる。
        """
        return frame.copy()
    
    def _filter_by_led_y_range(
        self,
        slit_coords_arr: np.ndarray,
        led_frame_points,
    ) -> np.ndarray:
        """
        LED投影位置のy座標から有効範囲を計算し、範囲外のスリット光点を除去する。

        有効範囲:
          - 上限 = y_top    - (y_2nd_top  - y_top)
          - 下限 = y_bottom + (y_bottom   - y_2nd_bottom)

        led_frame_points が None / 点数が2未満の場合はフィルタしない。
        """
        if led_frame_points is None:
            return slit_coords_arr

        try:
            coords = led_frame_points.coords_in_frame
        except AttributeError:
            return slit_coords_arr

        if coords is None or len(coords) < 2:
            return slit_coords_arr

        y_sorted = np.sort(coords[:, 1])

        y_top         = float(y_sorted[0])
        y_2nd_top     = float(y_sorted[1])
        y_bottom      = float(y_sorted[-1])
        y_2nd_bottom  = float(y_sorted[-2])

        y_min_valid = y_top    - (y_2nd_top  - y_top)
        y_max_valid = y_bottom + (y_bottom   - y_2nd_bottom)

        slit_y = slit_coords_arr[:, 1].astype(float)
        mask = (slit_y >= y_min_valid) & (slit_y <= y_max_valid)

        if self.logger:
            removed = int((~mask).sum())
            if removed > 0:
                self.logger.debug(
                    f"LED y範囲フィルタ: 有効範囲 y=[{y_min_valid:.1f}, {y_max_valid:.1f}], "
                    f"{removed}点を除去"
                )

        return slit_coords_arr[mask]

    def _extract_center_per_row(
        self,
        binary: np.ndarray,
        brightness: np.ndarray,
    ) -> list:
        """
        各 y 行について、輝度の重心 x を求める。

        Parameters
        ----------
        binary : np.ndarray
            二値化マスク (H, W), bool
        brightness : np.ndarray
            グレースケール輝度値 (H, W), uint8

        Returns
        -------
        list of (x, y)
        """
        points = []
        h = binary.shape[0]

        for y in range(h):
            bright_x = np.where(binary[y])[0]
            if len(bright_x) < self.min_bright_pixels:
                continue

            weights = brightness[y, bright_x].astype(np.float32)
            weight_sum = weights.sum()
            if weight_sum == 0:
                continue

            center_x = int(np.round(np.dot(bright_x.astype(np.float32), weights) / weight_sum))
            points.append((center_x, y))

        return points
    
    def _get_z_from_mapping(
        self,
        y_value: float,
        mapping_info: Optional[dict],
    ) -> Optional[float]:
        """
        LED y-z マッピングからz座標を取得する。

        範囲内: 補間テーブルを使用。
        範囲外: 端の折れ線セグメントの傾きを継続して外挿する。
        """
        
        if mapping_info is None:
            return None
        
        try:
            y_range = mapping_info.get('y_range')
            z_interp = mapping_info.get('z_interp')
            y_min = mapping_info.get('y_min')
            y_max = mapping_info.get('y_max')
            
            if y_range is None or z_interp is None:
                return None
            
            if y_value < y_min:
                # 先端折れ線の傾きで外挿
                dy = y_range[1] - y_range[0]
                if abs(dy) < 1e-10:
                    return float(z_interp[0])
                slope = (z_interp[1] - z_interp[0]) / dy
                return float(z_interp[0] + slope * (y_value - y_range[0]))
            
            if y_value > y_max:
                # 末端折れ線の傾きで外挿
                dy = y_range[-1] - y_range[-2]
                if abs(dy) < 1e-10:
                    return float(z_interp[-1])
                slope = (z_interp[-1] - z_interp[-2]) / dy
                return float(z_interp[-1] + slope * (y_value - y_range[-1]))
            
            # 範囲内は補間テーブルをそのまま使用
            z_value = np.interp(y_value, y_range, z_interp)
            return float(z_value)
            
        except Exception as e:
            if self.logger:
                self.logger.exception(f"z値取得エラー: {e}")
            return None

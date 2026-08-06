"""
LED フレーム-ワールド座標マッパーサービス

画像座標のy値と実空間座標のz値を紐づけ、
線形補間で値がない部分を埋める。
"""

from __future__ import annotations
from typing import Tuple, Optional
import numpy as np
from logging import Logger

from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame
from domain.value_objects.computed_values.led_world_coordinates_in_frame import LedWorldCoordinatesInFrame


class LedFrameToWorldMapperService:
    """
    LED画像座標のy値と実空間座標のz値を紐づけるサービス。
    
    画像上でy座標が小さいほど実空間座標のz値が大きいという対応付けを行う。
    検出されなかった部分は線形補間で埋める。
    """
    
    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger
    
    def create_mapping(
        self,
        led_points_in_frame: RedBrightPointsInFrame,
        led_world_coords: LedWorldCoordinatesInFrame,
    ) -> Tuple[bool, Optional[np.ndarray]]:
        """
        LED画像座標のy値と実空間座標のz値の対応を作成する。
        
        Parameters
        ----------
        led_points_in_frame : RedBrightPointsInFrame
            検出されたLED点の画像座標 (x, y)
        led_world_coords : LedWorldCoordinatesInFrame
            LED番号に対応する実空間座標 (x, y, z)
            
        Returns
        -------
        (success, y_to_z_mapping)
            success : bool
            y_to_z_mapping : np.ndarray
                y座標（画像座標）をキーとして、z座標（実空間）を返すマッピング関数の係数
                または補間テーブル
        """
        
        try:
            coords_frame = led_points_in_frame.coords_in_frame  # (N, 2)
            coords_world = led_world_coords.coords_in_world      # (N, 3)
            
            if coords_frame is None or coords_world is None:
                if self.logger:
                    self.logger.error("入力座標が None です")
                return False, None
            
            if len(coords_frame) == 0 or len(coords_world) == 0:
                if self.logger:
                    self.logger.error("入力座標が空です")
                return False, None
            
            # 画像座標のy値と実空間座標のz値を抽出
            y_frame = coords_frame[:, 1]  # 画像座標y
            z_world = coords_world[:, 2]   # 実空間座標z
            
            # y座標の昇順でソート
            sort_indices = np.argsort(y_frame)
            y_sorted = y_frame[sort_indices]
            z_sorted = z_world[sort_indices]
            
            # y座標とz座標の線形関係を求める
            # z = a * y + b の形で近似
            # ただし、y座標が反転しているため、y_imageが大きいほどz_worldが小さい
            
            # 最小二乗法で係数を求める
            A = np.vstack([y_sorted, np.ones(len(y_sorted))]).T
            coeffs, _, _, _ = np.linalg.lstsq(A, z_sorted, rcond=None)
            
            if self.logger:
                self.logger.info(
                    f"LED y-z マッピング作成: "
                    f"点数={len(y_sorted)}, "
                    f"係数 a={coeffs[0]:.6f}, b={coeffs[1]:.6f}"
                )
            
            # 補間テーブルを作成（より正確な補間のため）
            # y座標の最小値から最大値まで細かく補間
            y_min, y_max = y_sorted[0], y_sorted[-1]
            y_range = np.linspace(y_min, y_max, 1000)
            z_interp = np.interp(y_range, y_sorted, z_sorted, 
                                left=z_sorted[0], right=z_sorted[-1])
            
            # マッピング情報を返す
            mapping_info = {
                'y_range': y_range,
                'z_interp': z_interp,
                'y_min': y_min,
                'y_max': y_max,
                'coeffs': coeffs,  # 係数も保持（参考用）
            }
            
            return True, mapping_info
            
        except Exception as e:
            if self.logger:
                self.logger.exception(f"LED y-z マッピング作成エラー: {e}")
            return False, None
    
    def get_z_for_y(
        self,
        y_value: float,
        mapping_info: dict
    ) -> Optional[float]:
        """
        画像座標のy値から実空間座標のz値を取得する。
        
        Parameters
        ----------
        y_value : float
            画像座標のy値
        mapping_info : dict
            create_mapping() で取得したマッピング情報
            
        Returns
        -------
        z_value : float, optional
            対応する実空間座標のz値
        """
        
        if mapping_info is None:
            return None
        
        try:
            y_range = mapping_info['y_range']
            z_interp = mapping_info['z_interp']
            y_min = mapping_info['y_min']
            y_max = mapping_info['y_max']
            
            # 範囲外チェック
            if y_value < y_min or y_value > y_max:
                if self.logger:
                    self.logger.warning(
                        f"y値がマッピング範囲外: y={y_value}, "
                        f"range=[{y_min}, {y_max}]"
                    )
                # 範囲外は端の値を返す
                if y_value < y_min:
                    return z_interp[0]
                else:
                    return z_interp[-1]
            
            # 線形補間
            z_value = np.interp(y_value, y_range, z_interp)
            return float(z_value)
            
        except Exception as e:
            if self.logger:
                self.logger.exception(f"z値取得エラー: {e}")
            return None

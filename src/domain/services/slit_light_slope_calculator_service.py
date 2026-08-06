"""
スリット光勾配計算サービス

スリット光の法線ベクトルから勾配角度を計算する。
既存のSlopeCalculatorServiceと同じロジックを使用。
"""

from __future__ import annotations
from typing import Tuple, Optional
import numpy as np
from logging import Logger

from domain.value_objects.computed_values.normal_vectors import NormalVectors
from domain.value_objects.computed_values.slope_angles import SlopeAngles


class SlitLightSlopeCalculatorService:
    """
    スリット光の法線ベクトル群から勾配角度を計算するサービス
    
    既存のSlopeCalculatorServiceと同じ計算式を使用。
    """
    
    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger
    
    def calculate(
        self,
        normals: NormalVectors
    ) -> Tuple[bool, Optional[SlopeAngles]]:
        """
        法線ベクトルから勾配角度を計算する。
        
        Parameters
        ----------
        normals : NormalVectors
            法線ベクトル群（shape=(N,3)）
            
        Returns
        -------
        (success, slope_angles)
            success : bool
            slope_angles : SlopeAngles
                X・Y方向の勾配角度（度数法）
        """
        
        try:
            if normals.normals_in_world is None or len(normals.normals_in_world) == 0:
                if self.logger:
                    self.logger.error("法線ベクトルが空です")
                return False, None
            
            normals_np = normals.normals_in_world
            slopes_deg = []
            
            for n in normals_np:
                # --- 入力チェック ---
                if n.shape != (3,) or np.isnan(n).any():
                    slopes_deg.append([np.nan, np.nan])
                    continue
                
                nx, ny, nz = n
                
                if abs(nz) < 1e-10:
                    slopes_deg.append([np.nan, np.nan])
                    continue
                
                # --- 勾配計算（既存と同じ計算式） ---
                # x勾配 = -arctan(nx / nz)
                # y勾配 = -arctan(ny / nz)
                
                x_slope_deg = -np.degrees(np.arctan2(nx, nz))
                y_slope_deg = -np.degrees(np.arctan2(ny, nz))
                
                slopes_deg.append([x_slope_deg, y_slope_deg])
            
            slopes_np_deg = np.array(slopes_deg, dtype=np.float64)
            
            # SlopeAngles を生成
            slopes_vo_deg = SlopeAngles.create(slopes_np_deg)
            if not slopes_vo_deg:
                if self.logger:
                    self.logger.error("SlopeAngles の生成に失敗")
                return False, None
            
            if self.logger:
                self.logger.info(
                    f"スリット光勾配計算成功: {len(slopes_np_deg)}個の勾配"
                )
            
            return True, slopes_vo_deg
            
        except Exception as e:
            if self.logger:
                self.logger.exception(f"スリット光勾配計算エラー: {e}")
            return False, None

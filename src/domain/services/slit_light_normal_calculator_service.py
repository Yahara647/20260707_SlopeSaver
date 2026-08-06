"""
スリット光法線計算サービス

スリット光源位置・投影位置・カメラ座標から法線ベクトルを計算する。
既存のReflectionNormalCalculatorServiceと同じロジックを用いる。
"""

from __future__ import annotations
from typing import Tuple, Optional
import numpy as np
from logging import Logger

from domain.value_objects.computed_values.slit_light_points_in_frame import SlitLightPointsInFrame
from domain.value_objects.computed_values.slit_light_points_in_world import SlitLightPointsInWorld
from domain.value_objects.config_values.camera_coordinate import CameraCoordinate
from domain.aggregates.app_config import AppConfig
from domain.value_objects.computed_values.normal_vectors import NormalVectors


class SlitLightNormalCalculatorService:
    """
    スリット光の法線計算サービス
    
    スリット光源位置、投影位置、カメラ座標から反射面の法線ベクトルを計算する。
    """
    
    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger
    
    def calculate(
        self,
        slit_light_source_in_world: np.ndarray,  # (N, 3) スリット光源の3D座標
        slit_projection_in_world: SlitLightPointsInWorld,  # 投影点の3D座標
        camera_coord: CameraCoordinate,
    ) -> Tuple[bool, Optional[NormalVectors]]:
        """
        スリット光の法線ベクトルを計算する。
        
        Parameters
        ----------
        slit_light_source_in_world : np.ndarray
            スリット光源の世界座標 (N, 3)
        slit_projection_in_world : SlitLightPointsInWorld
            スリット光の投影位置（反射点）の世界座標 (N, 3)
        camera_coord : CameraCoordinate
            カメラの世界座標
            
        Returns
        -------
        (success, normal_vectors)
            success : bool
            normal_vectors : NormalVectors
        """
        
        try:
            # --- 入力チェック ---
            if slit_projection_in_world.is_empty:
                if self.logger:
                    self.logger.error("投影位置が空です")
                return False, None
            
            if slit_light_source_in_world is None or len(slit_light_source_in_world) == 0:
                if self.logger:
                    self.logger.error("光源位置が空です")
                return False, None
            
            L = slit_light_source_in_world           # (N, 3) 光源位置
            P = slit_projection_in_world.coords_in_world  # (N, 3) 投影位置
            C = camera_coord.coord_in_world          # (3,) カメラ位置
            
            # サイズチェック
            if L.shape[0] != P.shape[0]:
                if self.logger:
                    self.logger.error(
                        f"光源と投影点の数が一致: "
                        f"L={L.shape[0]}, P={P.shape[0]}"
                    )
                return False, None
            
            normals = []
            
            for i in range(len(L)):
                bright = P[i]  # 投影点（反射点）
                led = L[i]     # 光源位置
                camera = C
                
                # --- 距離計算 ---
                d1 = np.linalg.norm(bright - led)
                d2 = np.linalg.norm(camera - bright)
                
                if d1 < 1e-10 or d2 < 1e-10:
                    if self.logger:
                        self.logger.warning(
                            f"距離がほぼ0: d1={d1}, d2={d2}"
                        )
                    normals.append([np.nan, np.nan, np.nan])
                    continue
                
                # --- カメラ → 反射点ベクトル ---
                camera_to_bright = bright - camera
                
                # --- 鏡像点（反射の法則を使用） ---
                scale = (d1 + d2) / d2
                mirror_led = camera + camera_to_bright * scale
                
                # --- 法線方向ベクトル ---
                n = led - mirror_led
                norm = np.linalg.norm(n)
                
                if norm < 1e-10:
                    if self.logger:
                        self.logger.warning(
                            f"法線ベクトルがほぼ0: norm={norm}"
                        )
                    normals.append([np.nan, np.nan, np.nan])
                else:
                    # 正規化
                    normals.append(n / norm)
            
            normals_np = np.array(normals, dtype=np.float64)
            
            # NormalVectors を生成
            normals_vo = NormalVectors.create(normals_np)
            if not normals_vo:
                if self.logger:
                    self.logger.error("NormalVectors の生成に失敗")
                return False, None
            
            if self.logger:
                self.logger.info(
                    f"スリット光法線計算成功: {len(normals)}個の法線ベクトル"
                )
            
            return True, normals_vo
            
        except Exception as e:
            if self.logger:
                self.logger.exception(f"スリット光法線計算エラー: {e}")
            return False, None

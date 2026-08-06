"""
スリット光ホモグラフィ変換サービス

スリット光の画像座標をホモグラフィ変換で実空間座標に変換する。
既に対応する光源z座標が分かっているため、xy座標変換後にzを付与する。
"""

from __future__ import annotations
from typing import Tuple, Optional
import numpy as np
from logging import Logger

from domain.value_objects.computed_values.slit_light_points_in_frame import SlitLightPointsInFrame
from domain.value_objects.computed_values.slit_light_source_z_coords import SlitLightSourceZCoords
from domain.value_objects.computed_values.slit_light_points_in_world import SlitLightPointsInWorld
from domain.value_objects.computed_values.homography_matrix import HomographyMatrix


class SlitLightTransformerService:
    """
    スリット光のホモグラフィ変換サービス
    
    スリット光の画像座標をホモグラフィ変換で実空間座標に変換する。
    """
    
    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger
    
    def transform_to_world(
        self,
        slit_points_in_frame: SlitLightPointsInFrame,
        slit_source_z_coords: SlitLightSourceZCoords,
        homography_matrix: HomographyMatrix,
        strip_z: float,
        reference_plane_z: float = 0.0,
    ) -> Tuple[bool, Optional[SlitLightPointsInWorld]]:
        """
        スリット光の画像座標を実空間座標に変換する。
        
        Parameters
        ----------
        slit_points_in_frame : SlitLightPointsInFrame
            画像座標のスリット光点（画像座標のみ）
        slit_source_z_coords : SlitLightSourceZCoords
            各点に対応するスリット光源のz座標（未使用）
        homography_matrix : HomographyMatrix
            ホモグラフィ行列
        strip_z : float
            スリット光が存在する平面のz座標（AppConfig.strip_z）
        reference_plane_z : float
            ホモグラフィが定義された参照平面のz値
            
        Returns
        -------
        (success, slit_points_in_world)
            success : bool
            slit_points_in_world : SlitLightPointsInWorld
        """
        
        try:
            if slit_points_in_frame.is_empty:
                if self.logger:
                    self.logger.warning("入力スリット光点が空です")
                empty = np.empty((0, 3), dtype=np.float64)
                slit_world = SlitLightPointsInWorld.create(empty)
                return True, slit_world
            
            frame_coords = slit_points_in_frame.coords_in_frame  # (N, 2)
            light_source_z = slit_source_z_coords.values          # (N,)
            
            # ホモグラフィ行列を取得
            H = homography_matrix.matrix  # (3, 3)
            
            world_coords = []
            
            for i, (px, py) in enumerate(frame_coords):
                # 画像座標を同次座標に変換
                p = np.array([px, py, 1.0], dtype=np.float64)
                
                # ホモグラフィ変換でxy座標を取得
                # （z=reference_plane_zの平面への射影）
                w = H @ p
                
                if abs(w[2]) < 1e-10:
                    if self.logger:
                        self.logger.warning(
                            f"ホモグラフィ変換の正規化エラー: "
                            f"点{i} (px={px}, py={py})"
                        )
                    continue
                
                # 正規化
                w /= w[2]
                
                # 変換後のxy座標にstrip_zをz座標として設定
                x_world = w[0]
                y_world = w[1]
                z_world = strip_z  # AppConfig.strip_zの値を使用
                
                world_coords.append([x_world, y_world, z_world])
            
            if len(world_coords) == 0:
                if self.logger:
                    self.logger.error("有効な実空間座標が得られません")
                return False, None
            
            world_coords_arr = np.array(world_coords, dtype=np.float64)
            
            # SlitLightPointsInWorldを生成
            slit_world = SlitLightPointsInWorld.create(world_coords_arr)
            if not slit_world:
                if self.logger:
                    self.logger.error("SlitLightPointsInWorld の生成に失敗")
                return False, None
            
            if self.logger:
                self.logger.info(
                    f"スリット光変換成功: {len(world_coords)}個の点を"
                    f"実空間座標に変換"
                )
            
            return True, slit_world
            
        except Exception as e:
            if self.logger:
                self.logger.exception(f"スリット光変換エラー: {e}")
            return False, None

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SlitLightPointsInWorld:
    """
    スリット光の点群を実空間座標系で保持するドメインモデル。
    
    ホモグラフィ変換により画像座標から実空間座標へ変換されている。
    
    - coords_in_world: 実空間座標 (x, y, z)
                       shape = (N, 3), dtype = float32/float64
                       各行が (x, y, z) を表す
    """
    
    coords_in_world: np.ndarray  # shape = (N, 3), float
    
    @property
    def is_empty(self) -> bool:
        """座標が0点なら True"""
        return self.coords_in_world is None or len(self.coords_in_world) == 0
    
    @classmethod
    def create(cls, coords_in_world: np.ndarray) -> "SlitLightPointsInWorld | False":
        """
        スリット光実空間座標を安全に生成するファクトリメソッド。
        
        Parameters
        ----------
        coords_in_world : np.ndarray
            実空間座標、shape=(N, 3), dtype=float
            
        Returns
        -------
        SlitLightPointsInWorld | False
        """
        
        # --- ndarray チェック ---
        if not isinstance(coords_in_world, np.ndarray):
            return False
        
        # --- shape チェック ---
        if coords_in_world.ndim != 2:
            return False
        if coords_in_world.shape[1] != 3:
            return False
        
        return cls(coords_in_world=coords_in_world.copy())

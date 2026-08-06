"""
スリット光源のy座標（実空間）
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class SlitLightSourceYCoordinate:
    """スリット光源のy座標（実空間、単位: mm）"""
    
    value: float
    
    @staticmethod
    def create(value: float) -> SlitLightSourceYCoordinate:
        """
        Creates SlitLightSourceYCoordinate instance.
        
        Parameters
        ----------
        value : float
            Y coordinate value in world space (mm)
            
        Returns
        -------
        SlitLightSourceYCoordinate
        """
        return SlitLightSourceYCoordinate(value=float(value))
    
    def to_dict(self) -> dict:
        return {"value": self.value}
    
    @staticmethod
    def from_dict(data: dict) -> SlitLightSourceYCoordinate:
        return SlitLightSourceYCoordinate.create(data.get("value", 0.0))

"""
スリット光源のx座標（実空間）
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class SlitLightSourceXCoordinate:
    """スリット光源のx座標（実空間、単位: mm）"""
    
    value: float
    
    @staticmethod
    def create(value: float) -> SlitLightSourceXCoordinate:
        """
        Creates SlitLightSourceXCoordinate instance.
        
        Parameters
        ----------
        value : float
            X coordinate value in world space (mm)
            
        Returns
        -------
        SlitLightSourceXCoordinate
        """
        return SlitLightSourceXCoordinate(value=float(value))
    
    def to_dict(self) -> dict:
        return {"value": self.value}
    
    @staticmethod
    def from_dict(data: dict) -> SlitLightSourceXCoordinate:
        return SlitLightSourceXCoordinate.create(data.get("value", 0.0))

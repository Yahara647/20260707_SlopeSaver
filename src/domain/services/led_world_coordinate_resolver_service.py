# src/domain/services/led_world_coordinate_resolver_service.py

from __future__ import annotations
from typing import Tuple
import numpy as np
from logging import Logger

from domain.value_objects.computed_values.led_numbers_in_frame import LedNumbersInFrame
from domain.value_objects.config_values.led_coordinates import LedCoordinates
from domain.value_objects.computed_values.led_world_coordinates_in_frame import LedWorldCoordinatesInFrame


class LedWorldCoordinateResolverService:
    """
    LedNumbersInFrame と LedCoordinates から、
    LED 番号に対応する世界座標を導出する Domain Service。
    """

    def __init__(self, logger: Logger | None = None) -> None:
        self.logger = logger

    def resolve(
        self,
        led_nums: LedNumbersInFrame,
        led_coordinates: LedCoordinates
    ) -> Tuple[bool, LedWorldCoordinatesInFrame | None]:
        """
        Parameters
        ----------
        led_nums : LedNumbersInFrame
            画像内で検出された LED 番号の集合
        led_coordinates : LedCoordinates
            全 LED の世界座標（index = LED 番号）

        Returns
        -------
        (success, world_coords_vo)
        """

        if led_nums.is_empty:
            if self.logger:
                self.logger.error("LedWorldCoordinateResolverService: led_nums が空です")
            return False, None

        coords_list = []

        for num in led_nums.led_nums:
            if 0 <= num < len(led_coordinates.coords_in_world):
                coords_list.append(led_coordinates.coords_in_world[num])
            else:
                # 範囲外 → NaN を返す
                coords_list.append(np.array([np.nan, np.nan, np.nan], dtype=float))

        coords_np = np.array(coords_list, dtype=float)

        world_coords_vo = LedWorldCoordinatesInFrame.create(coords_np)
        if world_coords_vo is False:
            if self.logger:
                self.logger.error("LedWorldCoordinateResolverService: VO 生成に失敗")
            return False, None

        return True, world_coords_vo

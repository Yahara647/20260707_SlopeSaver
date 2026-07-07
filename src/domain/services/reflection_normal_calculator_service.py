# src/domain/services/reflection_normal_calculator_service.py

from __future__ import annotations
from typing import Tuple
import numpy as np
from logging import Logger

from domain.value_objects.computed_values.led_world_coordinates_in_frame import LedWorldCoordinatesInFrame
from domain.value_objects.computed_values.red_bright_points_in_world import RedBrightPointsInWorld
from domain.value_objects.config_values.camera_coordinate import CameraCoordinate
from domain.value_objects.computed_values.normal_vectors import NormalVectors


class ReflectionNormalCalculatorService:
    """
    以前の NormalCalculator と同じ計算式で、
    LED・反射点・カメラ座標から反射面の法線ベクトルを求める Domain Service。
    """

    def __init__(self, logger: Logger | None = None) -> None:
        self.logger = logger

    def calculate(
        self,
        led_world_coords: LedWorldCoordinatesInFrame,
        red_world_coords: RedBrightPointsInWorld,
        camera_coord: CameraCoordinate
    ) -> Tuple[bool, NormalVectors | None]:
        """
        Parameters
        ----------
        led_world_coords : LedWorldCoordinatesInFrame
            LED の世界座標（shape=(N,3)）
        red_world_coords : RedBrightPointsInWorld
            反射点の世界座標（shape=(N,3)）
        camera_coord : CameraCoordinate
            カメラの世界座標（shape=(3,)）

        Returns
        -------
        (success, normal_vectors)
            success : bool
            normal_vectors : NormalVectors
        """

        # --- 入力チェック ---
        if led_world_coords.is_empty or red_world_coords.is_empty:
            if self.logger:
                self.logger.error("ReflectionNormalCalculatorService: 入力座標が空です")
            return False, None

        L = led_world_coords.coords_in_world      # shape=(N,3)
        P = red_world_coords.coords_in_world      # shape=(N,3)
        C = camera_coord.coord_in_world           # shape=(3,)

        if L.shape != P.shape:
            if self.logger:
                self.logger.error("ReflectionNormalCalculatorService: LED と反射点の数が一致しません")
            return False, None

        normals = []

        for i in range(len(L)):
            bright = P[i]
            led = L[i]
            camera = C

            # --- 距離計算 ---
            d1 = np.linalg.norm(bright - led)
            d2 = np.linalg.norm(camera - bright)

            if d1 == 0 or d2 == 0:
                normals.append([np.nan, np.nan, np.nan])
                continue

            # --- カメラ → 反射点ベクトル ---
            camera2bright = bright - camera

            # --- 鏡像点 ---
            scale = (d1 + d2) / d2
            mirror_led = camera + camera2bright * scale

            # --- 法線方向ベクトル ---
            n = led - mirror_led
            norm = np.linalg.norm(n)

            if norm == 0:
                normals.append([np.nan, np.nan, np.nan])
            else:
                normals.append(n / norm)

        normals_np = np.array(normals, dtype=float)

        normals_vo = NormalVectors.create(normals_np)
        if normals_vo is False:
            if self.logger:
                self.logger.error("ReflectionNormalCalculatorService: NormalVectors の生成に失敗")
            return False, None

        if self.logger:
            self.logger.debug("ReflectionNormalCalculatorService: 法線ベクトル計算完了")

        return True, normals_vo

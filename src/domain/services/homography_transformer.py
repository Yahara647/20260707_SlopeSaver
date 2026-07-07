import numpy as np
import cv2

from domain.value_objects.computed_values.homography_matrix import HomographyMatrix
from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame
from domain.value_objects.computed_values.red_bright_points_in_world import RedBrightPointsInWorld
from domain.value_objects.computed_values.calibration_leds_in_frame import CalibrationLedsInFrame
from domain.value_objects.config_values.calibration_leds_in_world import CalibrationLedsInWorld


class HomographyTransformer:
    """
    ホモグラフィ行列の生成と、
    画素座標 → 実空間座標変換を行うドメインサービス。
    """

    # ---------------------------------------------------------
    # ① ホモグラフィ行列の生成
    # ---------------------------------------------------------
    def compute_homography(
        self,
        calib_in_frame: CalibrationLedsInFrame,
        calib_in_world: CalibrationLedsInWorld
    ) -> HomographyMatrix:
        """
        キャリブレーション LED の pixel/world 対応から
        ホモグラフィ行列 H を生成して返す。
        """

        pixel = calib_in_frame.coords_in_frame          # shape=(N,2), int32
        world = calib_in_world.coords_in_world          # shape=(N,3), float64

        if pixel.shape[0] < 4:
            raise ValueError("ホモグラフィ行列生成には4点以上が必要")

        # world 座標は XY のみ使用
        world_xy = world[:, :2]

        H, status = cv2.findHomography(pixel, world_xy, method=0)

        if H is None:
            raise RuntimeError("ホモグラフィ行列の計算に失敗")

        return HomographyMatrix.create(H.astype(np.float64))


    # ---------------------------------------------------------
    # ② 画素座標 → 実空間座標変換
    # ---------------------------------------------------------
    def transform_points(
        self,
        H: HomographyMatrix,
        points_in_frame: RedBrightPointsInFrame,
        strip_z: float
    ) -> RedBrightPointsInWorld:
        """
        ホモグラフィ行列 H と RedBrightPointsInFrame を受け取り、
        Z=strip_z 平面に射影した実空間座標を返す。
        """

        if points_in_frame.is_empty:
            empty = np.empty((0, 3), dtype=np.float64)
            return RedBrightPointsInWorld.create(empty)

        pts = points_in_frame.coords_in_frame  # shape=(N,2)

        world_list = []

        for (px, py) in pts:
            p = np.array([px, py, 1.0], dtype=np.float64)
            w = H.matrix @ p

            if w[2] == 0:
                raise ZeroDivisionError("ホモグラフィ正規化エラー")

            w /= w[2]  # 正規化

            world_list.append([w[0], w[1], strip_z])

        world_arr = np.array(world_list, dtype=np.float64)

        return RedBrightPointsInWorld.create(world_arr)

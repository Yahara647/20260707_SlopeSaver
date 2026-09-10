# src/domain/services/red_light_detector.py

import cv2
import numpy as np

from domain.entities.rgb8_frame import Rgb8Frame
from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame


class RedLightDetector:
    """
    モノクロ画像から輝度の高い点を検出し、
    RedBrightPointsInFrame（ValueObject）として返すドメインサービス。

    旧来のカラー向け HSV 赤検出ロジックはモノクロカメラに対応していないため、
    明度閾値ベースの検出へ変更する。
    """

    def execute(
        self,
        frame: Rgb8Frame,
        value_th: int = 80,
        min_area: int = 50
    ) -> RedBrightPointsInFrame:
        """
        輝度閾値以上の明点を検出し、中心座標を RedBrightPointsInFrame として返す。

        Parameters
        ----------
        frame : Rgb8Frame
            モノクロ画像（HxW, uint8）を持つドメイン画像 ValueObject
        value_th : int
            輝度閾値（0〜255）
        min_area : int
            面積フィルタの下限

        Returns
        -------
        RedBrightPointsInFrame
        """

        if frame is None or not isinstance(frame, Rgb8Frame):
            return RedBrightPointsInFrame.create(np.empty((0, 2), dtype=np.int32))

        gray = frame.data
        if gray is None or gray.ndim != 2 or gray.dtype != np.uint8:
            return RedBrightPointsInFrame.create(np.empty((0, 2), dtype=np.int32))

        mask = (gray >= int(value_th)).astype(np.uint8)

        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.dilate(mask, np.ones((3, 7), np.uint8), iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        points = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            cx = x + w // 2
            cy = y + h // 2
            points.append((cx, cy))

        if len(points) == 0:
            return RedBrightPointsInFrame.create(np.empty((0, 2), dtype=np.int32))

        points = np.array(points, dtype=np.int32)
        points = points[np.argsort(points[:, 1])]

        return RedBrightPointsInFrame.create(points)

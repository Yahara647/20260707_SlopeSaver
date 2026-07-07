# src/domain/services/red_light_detector.py

import cv2
import numpy as np

from domain.entities.rgb8_frame import Rgb8Frame
from domain.value_objects.computed_values.red_bright_points_in_frame import RedBrightPointsInFrame


class RedLightDetector:
    """
    RGB8 フレームから赤色輝点を検出し、
    RedBrightPointsInFrame（ValueObject）として返すドメインサービス。
    """

    def execute(
        self,
        frame: Rgb8Frame,
        value_th: int = 80,
        min_area: int = 50
    ) -> RedBrightPointsInFrame:
        """
        赤色輝点を検出し、中心座標を RedBrightPointsInFrame として返す。

        Parameters
        ----------
        frame : Rgb8Frame
            ドメインの画像 ValueObject
        value_th : int
            HSV の V（明るさ）閾値
        min_area : int
            面積フィルタの下限

        Returns
        -------
        RedBrightPointsInFrame
        """

        # -------------------------
        # 入力チェック
        # -------------------------
        if frame is None or not isinstance(frame, Rgb8Frame):
            return RedBrightPointsInFrame.create(np.empty((0, 2), dtype=np.int32))

        bgr = frame.data  # ndarray (H, W, 3)

        # -------------------------
        # BGR → HSV
        # -------------------------
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        # -------------------------
        # 赤色マスク（2区間）
        # -------------------------
        lower_red1 = np.array([0, 80, value_th])
        upper_red1 = np.array([30, 255, 255])

        lower_red2 = np.array([150, 80, value_th])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)

        # -------------------------
        # 横方向の膨張（連結強化）
        # -------------------------
        horizontal_kernel = np.ones((3, 7), np.uint8)
        mask = cv2.dilate(mask, horizontal_kernel, iterations=1)

        # -------------------------
        # ノイズ除去
        # -------------------------
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # -------------------------
        # 輪郭抽出
        # -------------------------
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        points = []

        # -------------------------
        # 中心点計算
        # -------------------------
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            cx = x + w // 2
            cy = y + h // 2
            points.append((cx, cy))

        # -------------------------
        # 検出なし
        # -------------------------
        if len(points) == 0:
            return RedBrightPointsInFrame.create(np.empty((0, 2), dtype=np.int32))

        # -------------------------
        # y 座標でソート
        # -------------------------
        points = np.array(points, dtype=np.int32)
        points = points[np.argsort(points[:, 1])]

        # -------------------------
        # ValueObject に包んで返す
        # -------------------------
        return RedBrightPointsInFrame.create(points)

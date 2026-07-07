from __future__ import annotations
from typing import Tuple
from logging import Logger
import numpy as np

# --- 新しい単一点ドメインモデル ---
from domain.value_objects.computed_values.single_bright_point_in_frame import SingleBrightPointInFrame

# --- あなたのプロジェクトの型 ---
from application.services.led.led_control_service import LedControlService
from application.services.camera.camera_control_service import CameraControlService
from application.services.camera.camera_capture_service import CameraCaptureService
from application.services.image_processing.red_light_detection_service import RedLightDetectionService


class SingleLedPositionLocatorService:
    """
    指定した LED を 1 つだけ点灯し、
    撮像 → 輝点検出 を行い、
    その LED がどこに映っているかを返す Application Service。

    ※世界座標変換は行わない。
    ※撮像前に露光時間を変更し、撮像後に元に戻す。
    ※検出点が 0 個または 2 個以上の場合はエラーログを残し、success=False を返す。
    """

    def __init__(
        self,
        led_control_service: LedControlService,
        camera_control_service: CameraControlService,
        camera_capture_service: CameraCaptureService,
        red_light_detection_service: RedLightDetectionService,
        logger: Logger | None = None
    ) -> None:
        self.led_control = led_control_service
        self.camera_control = camera_control_service
        self.camera_capture = camera_capture_service
        self.detector = red_light_detection_service
        self.logger = logger

    # ---------------------------------------------------------
    # LED の位置を推定するメイン処理
    # ---------------------------------------------------------
    def locate(
        self,
        led_id: int,
        exposure_us: float
    ) -> Tuple[bool, SingleBrightPointInFrame | None]:
        """
        指定した LED を点灯 → 露光変更 → 撮像 → 輝点検出 → 露光復帰。

        Returns
        -------
        (success, point)
            success : bool
                True  → 検出点が 1 個で正常終了
                False → 検出点が 0 個 or 2 個以上 or 撮像失敗
            point : SingleBrightPointInFrame | None
                単一点の座標（正常時のみ）
        """

        # --- 現在の露光時間を保存 ---
        original_exposure: float = self.camera_control.get_exposure()

        # --- LED 点灯 ---
        self.led_control.turn_only(led_id)
        if self.logger:
            self.logger.debug(f"LED {led_id} を点灯")

        # --- 露光時間を一時変更 ---
        self.camera_control.set_exposure(exposure_us)
        if self.logger:
            self.logger.debug(f"露光時間を {exposure_us} us に変更")

        # --- 撮像 ---
        frame = self.camera_capture.capture_once()
        if frame is None:
            self.led_control.turn_off_all()
            self.camera_control.set_exposure(original_exposure)

            if self.logger:
                self.logger.error("SingleLedPositionLocatorService: 撮像に失敗しました")

            return False, None

        # --- 輝点検出（複数点の可能性あり） ---
        detected_points = self.detector.detect(frame)
        count: int = len(detected_points.coords_in_frame)

        # --- LED 消灯 ---
        self.led_control.turn_off_all()

        # --- 露光時間を元に戻す ---
        self.camera_control.set_exposure(original_exposure)
        if self.logger:
            self.logger.debug(f"露光時間を元の {original_exposure} us に復帰")

        # --- 検出数チェック ---
        if count == 0:
            if self.logger:
                self.logger.error(
                    f"SingleLedPositionLocatorService: LED {led_id} の輝点が検出されませんでした"
                )
            return False, None

        if count > 1:
            if self.logger:
                self.logger.error(
                    f"SingleLedPositionLocatorService: LED {led_id} の輝点が複数検出されました（{count} 個）"
                )
            return False, None

        # --- 正常（1点のみ検出） ---
        coord = detected_points.coords_in_frame.astype(np.int32)
        coord = coord.reshape(1, 2)

        point = SingleBrightPointInFrame.create(coord)
        if point is False:
            if self.logger:
                self.logger.error("SingleLedPositionLocatorService: SingleBrightPointInFrame の生成に失敗")
            return False, None

        if self.logger:
            x, y = point.coord_in_frame[0]
            self.logger.debug(
                f"SingleLedPositionLocatorService: LED {led_id} の位置を検出: ({x}, {y})"
            )

        return True, point

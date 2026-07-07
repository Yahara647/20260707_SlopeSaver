# src/infrastructure/camera/pylon_camera_driver.py

from domain.interfaces.i_camera_service import ICameraService
from domain.entities.rgb8_frame import Rgb8Frame
from infrastructure.camera.camera_state import CameraState
from pypylon import pylon
from datetime import datetime
import threading
import time
import cv2
from logger.logger import logger


class PylonCameraDriver(ICameraService):

    def __init__(self, state: CameraState):
        self.state = state
        self.logger = logger
        self.camera: pylon.InstantCamera | None = None

        # 全メソッド共通の排他ロック
        self._lock = threading.Lock()

    # ============================================================
    # initialize()
    # ============================================================
    def initialize(self) -> bool:
        with self._lock:
            try:
                self.logger.info("CameraDriver: 初期化開始")

                tl_factory = pylon.TlFactory.GetInstance()
                devices = tl_factory.EnumerateDevices()

                if len(devices) == 0:
                    self.logger.error("CameraDriver: Basler カメラが検出されませんでした")
                    return False

                device = devices[self.state.camera_index]
                self.logger.info(f"CameraDriver: 使用デバイス = {device.GetFriendlyName()}")

                self.camera = pylon.InstantCamera(tl_factory.CreateDevice(device))
                self.camera.Open()
                self.logger.info("CameraDriver: カメラ Open 成功")

                # --- UserSetDefault ---
                try:
                    if hasattr(self.camera, "UserSetSelector"):
                        self.camera.UserSetSelector.SetValue("Default")
                        self.camera.UserSetLoad.Execute()
                except Exception as e:
                    self.logger.warning(f"UserSetDefault ロード中に例外: {e}")

                # --- PixelFormat ---
                try:
                    self.camera.PixelFormat.SetValue("BayerRG8")
                except Exception as e:
                    self.logger.warning(f"PixelFormat 設定失敗: {e}")

                # --- ISP OFF ---
                try:
                    if hasattr(self.camera, "BalanceWhiteAuto"):
                        self.camera.BalanceWhiteAuto.SetValue("Off")
                    if hasattr(self.camera, "LightSourcePreset"):
                        self.camera.LightSourcePreset.SetValue("Off")
                    if hasattr(self.camera, "ColorAdjustmentEnable"):
                        self.camera.ColorAdjustmentEnable.SetValue(False)
                    if hasattr(self.camera, "GammaEnable"):
                        self.camera.GammaEnable.SetValue(False)
                    if hasattr(self.camera, "DemosaicingEnable"):
                        self.camera.DemosaicingEnable.SetValue(False)
                except Exception as e:
                    self.logger.warning(f"ISP 無効化中に例外: {e}")

                # --- ROI ---
                try:
                    if self.state.roi_width > 0 and self.state.roi_height > 0:
                        self.camera.OffsetX.SetValue(self.state.roi_x)
                        self.camera.OffsetY.SetValue(self.state.roi_y)
                        self.camera.Width.SetValue(self.state.roi_width)
                        self.camera.Height.SetValue(self.state.roi_height)
                except Exception as e:
                    self.logger.warning(f"ROI 設定中に例外: {e}")

                # --- AutoExposure / AutoGain ---
                try:
                    if hasattr(self.camera, "ExposureAuto"):
                        self.camera.ExposureAuto.SetValue("Continuous" if self.state.auto_exposure else "Off")
                    if hasattr(self.camera, "GainAuto"):
                        self.camera.GainAuto.SetValue("Continuous" if self.state.auto_gain else "Off")
                except Exception as e:
                    self.logger.warning(f"Auto 設定中に例外: {e}")

                # --- Exposure / Gain ---
                try:
                    if not self.state.auto_exposure:
                        self.camera.ExposureTime.SetValue(self.state.exposure_time)
                    if not self.state.auto_gain:
                        self.camera.Gain.SetValue(self.state.gain)
                except Exception as e:
                    self.logger.warning(f"露光/ゲイン設定中に例外: {e}")

                # --- Grab 開始 ---
                self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
                self.state.is_initialized = True

                return True

            except Exception as e:
                self.logger.exception(f"CameraDriver: 初期化中に例外発生: {e}")
                return False

    # ============================================================
    # capture()
    # ============================================================
    def capture(self) -> Rgb8Frame | None:
        with self._lock:
            if self.camera is None:
                self.logger.error("CameraDriver: capture() 呼び出し時に camera が None")
                return None

            try:
                grab = self.camera.RetrieveResult(self.state.timeout, pylon.TimeoutHandling_Return)

                if grab is None or not grab.GrabSucceeded():
                    self.logger.error("CameraDriver: Grab 失敗")
                    return None

                bayer = grab.Array
                grab.Release()

                rgb = cv2.cvtColor(bayer, cv2.COLOR_BAYER_RG2RGB)
                return Rgb8Frame.create(rgb, datetime.now())

            except Exception as e:
                self.logger.exception(f"CameraDriver: capture() 中に例外発生: {e}")
                return None

    # ============================================================
    # set_exposure_time()
    # ============================================================
    def set_exposure_time(self, exposure_us: float) -> bool:
        with self._lock:
            try:
                # 露光変更
                exp = float(exposure_us)
                self.camera.ExposureAuto.SetValue("Off")
                self.camera.ExposureTime.SetValue(exp)
                self.state.exposure_time = exp

                # ---------------------------------------------------------
                # ★ Basler の仕様：露光変更後 2〜3 フレームは古い露光のまま
                #    → ここで捨てフレームを行う
                # ---------------------------------------------------------
                for i in range(3):
                    grab = self.camera.RetrieveResult(self.state.timeout, pylon.TimeoutHandling_Return)
                    if grab is not None and grab.GrabSucceeded():
                        grab.Release()
                    else:
                        self.logger.warning("CameraDriver: set_exposure_time() 捨てフレーム取得失敗")

                return True

            except Exception as e:
                self.logger.error(f"露光設定失敗: {e}")
                return False

    # ============================================================
    # set_roi()
    # ============================================================
    def set_roi(self, x: int, y: int, w: int, h: int) -> bool:
        with self._lock:
            try:
                nodemap = self.camera.GetNodeMap()

                if self.camera.IsGrabbing():
                    self.camera.StopGrabbing()

                offset_x = nodemap.GetNode("OffsetX")
                offset_y = nodemap.GetNode("OffsetY")
                width_node = nodemap.GetNode("Width")
                height_node = nodemap.GetNode("Height")

                inc_w = width_node.GetInc()
                inc_h = height_node.GetInc()
                inc_x = offset_x.GetInc()
                inc_y = offset_y.GetInc()

                w = (w // inc_w) * inc_w
                h = (h // inc_h) * inc_h
                x = (x // inc_x) * inc_x
                y = (y // inc_y) * inc_y

                offset_x.SetValue(0)
                offset_y.SetValue(0)
                width_node.SetValue(w)
                height_node.SetValue(h)
                offset_x.SetValue(x)
                offset_y.SetValue(y)

                self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
                return True

            except Exception as e:
                self.logger.error(f"ROI 設定失敗: {e}")
                if not self.camera.IsGrabbing():
                    self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
                return False

    def get_max_resolution(self) -> tuple[int, int]:
        with self._lock:
            if self.camera is None:
                raise RuntimeError("Camera not initialized")

            nodemap = self.camera.GetNodeMap()
            width_node = nodemap.GetNode("Width")
            height_node = nodemap.GetNode("Height")

            max_w = width_node.GetMax()
            max_h = height_node.GetMax()

            return max_w, max_h

    def capture_with_exposure(self, exposure_us: float) -> Rgb8Frame | None:
        """
        指定露光で1枚撮像し、撮像後に元の露光に戻す。
        露光変更 → 捨てフレーム → 本番撮像 → 露光復帰 を
        すべて排他ロック内で行うため、他スレッドが割り込めない。
        """
        with self._lock:
            if self.camera is None:
                self.logger.error("CameraDriver: capture_with_exposure() 呼び出し時に camera が None")
                return None

            try:
                # 現在の露光を保存
                original_exposure = self.state.exposure_time

                # 必要なら露光を変更
                exposure_changed = False
                if original_exposure != exposure_us:
                    try:
                        # ★ Basler は numpy 型を受け付けないため、必ず Python float に変換する
                        exp = float(exposure_us)

                        self.camera.ExposureAuto.SetValue("Off")
                        self.camera.ExposureTime.SetValue(exp)
                        self.state.exposure_time = exp
                        exposure_changed = True
                    except Exception as e:
                        self.logger.error(f"一時露光設定失敗: {e}")
                        return None

                # ---------------------------------------------------------
                # ★ 捨てフレーム（Basler は露光変更後 2〜3 フレームが古い露光のまま）
                # ---------------------------------------------------------
                for i in range(3):
                    grab = self.camera.RetrieveResult(self.state.timeout, pylon.TimeoutHandling_Return)
                    if grab is not None and grab.GrabSucceeded():
                        grab.Release()
                    else:
                        self.logger.warning("CameraDriver: 捨てフレーム取得失敗")

                # ---------------------------------------------------------
                # ★ 本番撮像
                # ---------------------------------------------------------
                grab = self.camera.RetrieveResult(self.state.timeout, pylon.TimeoutHandling_Return)

                if grab is None or not grab.GrabSucceeded():
                    self.logger.error("CameraDriver: Grab 失敗")
                    return None

                bayer = grab.Array
                grab.Release()

                rgb = cv2.cvtColor(bayer, cv2.COLOR_BAYER_RG2RGB)
                frame = Rgb8Frame.create(rgb, datetime.now())

                # ---------------------------------------------------------
                # ★ 元の露光に戻す
                # ---------------------------------------------------------
                if exposure_changed:
                    try:
                        self.camera.ExposureTime.SetValue(float(original_exposure))
                        self.state.exposure_time = original_exposure
                    except Exception as e:
                        self.logger.error(f"露光復帰失敗: {e}")

                return frame

            except Exception as e:
                self.logger.exception(f"capture_with_exposure() 中に例外発生: {e}")
                return None

    # ============================================================
    # close()
    # ============================================================
    def close(self) -> None:
        with self._lock:
            if self.camera is not None:
                try:
                    if self.camera.IsGrabbing():
                        self.camera.StopGrabbing()
                    self.camera.Close()
                except Exception as e:
                    self.logger.exception(f"CameraDriver: close() 中に例外発生: {e}")

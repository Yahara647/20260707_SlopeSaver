# src/infrastructure/camera/pylon_camera_driver.py

from domain.interfaces.i_camera_service import ICameraService
from domain.entities.rgb8_frame import Rgb8Frame
from infrastructure.camera.camera_state import CameraState
from pypylon import pylon
from datetime import datetime
import threading
import time
import cv2
import numpy as np
from logger.logger import logger


class PylonCameraDriver(ICameraService):

    def __init__(self, state: CameraState):
        self.state = state
        self.logger = logger
        self.camera: pylon.InstantCamera | None = None

        # 全メソッド共通の排他ロック
        self._lock = threading.Lock()

    def _get_node(self, node_name: str):
        if self.camera is None:
            return None
        try:
            nodemap = self.camera.GetNodeMap()
            return nodemap.GetNode(node_name)
        except Exception:
            return None

    def _set_enum_value(self, node_name: str, value, *, allow_missing: bool = True) -> bool:
        node = self._get_node(node_name)
        if node is None:
            if allow_missing:
                return False
            raise RuntimeError(f"Node not existing: {node_name}")

        try:
            node.SetValue(value)
            return True
        except Exception as e:
            if allow_missing:
                self.logger.warning(f"{node_name} 設定失敗: {e}")
                return False
            raise

    def _set_float_value(self, node_name: str, value: float, *, allow_missing: bool = True) -> bool:
        node = self._get_node(node_name)
        if node is None:
            if allow_missing:
                return False
            raise RuntimeError(f"Node not existing: {node_name}")

        try:
            node.SetValue(float(value))
            return True
        except Exception as e:
            if allow_missing:
                self.logger.warning(f"{node_name} 設定失敗: {e}")
                return False
            raise

    def _set_exposure_value(self, exposure_us: float) -> bool:
        if self.camera is None:
            return False

        try:
            if self._set_enum_value("ExposureAuto", "Off", allow_missing=True):
                pass

            exposure_node = self._get_node("ExposureTime")
            if exposure_node is None:
                exposure_node = self._get_node("ExposureTimeAbs")
            if exposure_node is None:
                raise RuntimeError("ExposureTime / ExposureTimeAbs node not available")

            exposure_node.SetValue(float(exposure_us))
            self.state.exposure_time = float(exposure_us)
            return True
        except Exception as e:
            self.logger.error(f"露光設定失敗: {e}")
            return False

    def _set_gain_value(self, gain_value: float) -> bool:
        if self.camera is None:
            return False

        gain_node = self._get_node("Gain")
        if gain_node is None:
            gain_node = self._get_node("GainRaw")
        if gain_node is None:
            return False

        try:
            gain_node.SetValue(float(gain_value))
            self.state.gain = float(gain_value)
            return True
        except Exception as e:
            self.logger.warning(f"Gain 設定失敗: {e}")
            return False

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
                    user_set_selector = self._get_node("UserSetSelector")
                    if user_set_selector is not None:
                        user_set_selector.SetValue("Default")
                        user_set_load = self._get_node("UserSetLoad")
                        if user_set_load is not None:
                            user_set_load.Execute()
                except Exception as e:
                    self.logger.warning(f"UserSetDefault ロード中に例外: {e}")

                # --- PixelFormat ---
                try:
                    pixel_format = self._get_node("PixelFormat")
                    if pixel_format is not None:
                        for candidate in ("Mono8", "BayerRG8"):
                            try:
                                pixel_format.SetValue(candidate)
                                self.logger.info(f"PixelFormat を {candidate} に設定しました")
                                break
                            except Exception as e:
                                self.logger.warning(f"PixelFormat={candidate} 設定失敗: {e}")
                    else:
                        self.logger.warning("PixelFormat node が存在しません。モノクロ前提で継続します")
                except Exception as e:
                    self.logger.warning(f"PixelFormat 設定中に例外: {e}")

                # --- ISP OFF ---
                try:
                    for node_name in ("BalanceWhiteAuto", "LightSourcePreset", "ColorAdjustmentEnable", "GammaEnable", "DemosaicingEnable"):
                        node = self._get_node(node_name)
                        if node is None:
                            continue
                        try:
                            if node_name in ("BalanceWhiteAuto", "LightSourcePreset"):
                                node.SetValue("Off")
                            elif node_name in ("ColorAdjustmentEnable", "GammaEnable", "DemosaicingEnable"):
                                node.SetValue(False)
                        except Exception as e:
                            self.logger.warning(f"{node_name} 無効化失敗: {e}")
                except Exception as e:
                    self.logger.warning(f"ISP 無効化中に例外: {e}")

                # --- ROI ---
                try:
                    if self.state.roi_width > 0 and self.state.roi_height > 0:
                        offset_x = self._get_node("OffsetX")
                        offset_y = self._get_node("OffsetY")
                        width_node = self._get_node("Width")
                        height_node = self._get_node("Height")
                        if offset_x is not None and offset_y is not None and width_node is not None and height_node is not None:
                            offset_x.SetValue(self.state.roi_x)
                            offset_y.SetValue(self.state.roi_y)
                            width_node.SetValue(self.state.roi_width)
                            height_node.SetValue(self.state.roi_height)
                except Exception as e:
                    self.logger.warning(f"ROI 設定中に例外: {e}")

                # --- AutoExposure / AutoGain ---
                try:
                    exposure_auto = self._get_node("ExposureAuto")
                    if exposure_auto is not None:
                        exposure_auto.SetValue("Continuous" if self.state.auto_exposure else "Off")
                    gain_auto = self._get_node("GainAuto")
                    if gain_auto is not None:
                        gain_auto.SetValue("Continuous" if self.state.auto_gain else "Off")
                except Exception as e:
                    self.logger.warning(f"Auto 設定中に例外: {e}")

                # --- Exposure / Gain ---
                try:
                    if not self.state.auto_exposure:
                        self._set_exposure_value(self.state.exposure_time)
                    if not self.state.auto_gain:
                        self._set_gain_value(self.state.gain)
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

                raw = grab.Array
                grab.Release()

                if raw is None:
                    return None

                if raw.ndim == 2:
                    frame = raw.astype(np.uint8, copy=False)
                elif raw.ndim == 3 and raw.shape[2] == 3:
                    frame = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
                elif raw.ndim == 2 and raw.dtype != np.uint8:
                    frame = raw.astype(np.uint8, copy=False)
                else:
                    try:
                        frame = cv2.cvtColor(raw, cv2.COLOR_BAYER_RG2GRAY)
                    except Exception:
                        frame = raw.astype(np.uint8, copy=False)

                return Rgb8Frame.create(frame, datetime.now())

            except Exception as e:
                self.logger.exception(f"CameraDriver: capture() 中に例外発生: {e}")
                return None

    # ============================================================
    # set_exposure_time()
    # ============================================================
    def set_exposure_time(self, exposure_us: float) -> bool:
        with self._lock:
            try:
                if self.camera is None:
                    return False

                exp = float(exposure_us)
                if not self._set_exposure_value(exp):
                    return False

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
                original_exposure = float(self.state.exposure_time)
                exposure_changed = False

                if abs(original_exposure - float(exposure_us)) > 1e-9:
                    try:
                        exp = float(exposure_us)
                        if not self._set_exposure_value(exp):
                            self.logger.error("一時露光設定失敗: ExposureTime/ExposureTimeAbs node not available")
                            return None
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

                raw = grab.Array
                grab.Release()

                if raw is None:
                    return None

                if raw.ndim == 2:
                    frame_array = raw.astype(np.uint8, copy=False)
                elif raw.ndim == 3 and raw.shape[2] == 3:
                    frame_array = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
                else:
                    try:
                        frame_array = cv2.cvtColor(raw, cv2.COLOR_BAYER_RG2GRAY)
                    except Exception:
                        frame_array = raw.astype(np.uint8, copy=False)

                frame = Rgb8Frame.create(frame_array, datetime.now())

                # ---------------------------------------------------------
                # ★ 元の露光に戻す
                # ---------------------------------------------------------
                if exposure_changed:
                    try:
                        self._set_exposure_value(float(original_exposure))
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

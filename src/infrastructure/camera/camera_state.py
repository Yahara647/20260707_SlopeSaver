from dataclasses import dataclass


@dataclass
class CameraState:
    # --- 初期化状態 ---
    is_initialized: bool = False

    # --- カメラ設定 ---
    exposure_time: float = 5000.0
    gain: float = 0.0
    timeout: int = 10000
    camera_index: int = 0

    # --- ROI ---
    roi_x: int = 0
    roi_y: int = 0
    roi_width: int = 0
    roi_height: int = 0

    # --- Auto ---
    auto_exposure: bool = False
    auto_gain: bool = False

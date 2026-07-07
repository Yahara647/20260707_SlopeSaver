# src/domain/value_objects/config_values/app_flags.py

from dataclasses import dataclass

@dataclass(frozen=True)
class AppFlags:
    """
    アプリ動作を制御するフラグ群。
    設定値として AppConfig に含める。
    """

    shutdown: bool = False
    pause: bool = False
    display_enabled: bool = True
    
    save_mode: str = "none"   # "none" / "image_only" / "image_and_result"

    highlight_enabled: bool = False

    graph_enabled: bool = False
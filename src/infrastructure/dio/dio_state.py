from dataclasses import dataclass

@dataclass
class DioState:
    host: str = "169.254.136.100"
    timeout: float = 1.0
    output_num: int = 32
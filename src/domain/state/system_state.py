from dataclasses import dataclass
import numpy as np

@dataclass
class SystemState:
    shutdown_flag: bool = False
from dataclasses import dataclass

@dataclass(frozen=True)
class WindowSize:
    width: int
    height: int

    @classmethod
    def create(cls, width: int, height: int):
        # --- 型チェック ---
        if not isinstance(width, int) or not isinstance(height, int):
            return None

        # --- 正の値チェック ---
        if width <= 0 or height <= 0:
            return None

        return cls(width=width, height=height)

    def as_tuple(self) -> tuple[int, int]:
        return (self.width, self.height)

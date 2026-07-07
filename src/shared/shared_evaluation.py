# shared/shared_evaluation.py
from threading import Lock

class SharedEvaluation:
    def __init__(self):
        self.lock = Lock()

        # 歪み量スコア
        self.slope_score: float | None = None

        # 最大歪み点 index
        self.slope_score_index: int | None = None

        # 画像上で強調表示する点 (x, y)
        self.highlight_point: tuple[int, int] | None = None

shared_evaluation = SharedEvaluation()

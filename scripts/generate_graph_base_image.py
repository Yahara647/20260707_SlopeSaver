from __future__ import annotations

from pathlib import Path
import cv2
import numpy as np

CANVAS_W = 600
CANVAS_H = 400
GLOBAL_SCALE = 0.95
CENTER_X = CANVAS_W / 2.0
CENTER_Y = CANVAS_H / 2.0

OBJECT_OFFSET_Y = 199


def tp(x: int, y: int) -> tuple[int, int]:
    """Scale a point around canvas center to add margins without breaking layout."""
    sx = int(round(CENTER_X + (x - CENTER_X) * GLOBAL_SCALE))
    sy = int(round(CENTER_Y + (y - CENTER_Y) * GLOBAL_SCALE))
    return sx, sy


def sv(v: int) -> int:
    return max(1, int(round(v * GLOBAL_SCALE)))


def draw_left_reference_panel(img: np.ndarray) -> None:
    # Five red markers
    ys = (np.linspace(62, 183, 5) + OBJECT_OFFSET_Y).astype(int)
    for y in ys:
        cv2.circle(img, tp(54, int(y)), sv(6), (0, 0, 255), -1)
        cv2.circle(img, tp(54, int(y)), sv(6), (30, 30, 120), 2)

    # Left vertical rectangle (drawn after circles so the rectangle is on top)
    cv2.rectangle(img, tp(1, 45 + OBJECT_OFFSET_Y), tp(54, 200 + OBJECT_OFFSET_Y), (220, 220, 220), -1)
    cv2.rectangle(img, tp(1, 45 + OBJECT_OFFSET_Y), tp(54, 200 + OBJECT_OFFSET_Y), (80, 80, 80), 2)


def draw_right_camera_icon(img: np.ndarray) -> None:
    # Camera body
    cv2.rectangle(img, tp(538, 110 + OBJECT_OFFSET_Y), tp(598, 155 + OBJECT_OFFSET_Y), (200, 200, 200), -1)
    cv2.rectangle(img, tp(538, 110 + OBJECT_OFFSET_Y), tp(598, 155 + OBJECT_OFFSET_Y), (70, 70, 70), 2)

    # Lens housing
    cv2.rectangle(img, tp(522, 122 + OBJECT_OFFSET_Y), tp(538, 144 + OBJECT_OFFSET_Y), (185, 185, 185), -1)
    cv2.rectangle(img, tp(522, 122 + OBJECT_OFFSET_Y), tp(538, 144 + OBJECT_OFFSET_Y), (70, 70, 70), 2)

    # Lens
    cv2.circle(img, tp(530, 133 + OBJECT_OFFSET_Y), sv(6), (120, 120, 120), -1)
    cv2.circle(img, tp(530, 133 + OBJECT_OFFSET_Y), sv(6), (60, 60, 60), 2)

    # Top mount
    cv2.rectangle(img, tp(553, 100 + OBJECT_OFFSET_Y), tp(584, 110 + OBJECT_OFFSET_Y), (180, 180, 180), -1)
    cv2.rectangle(img, tp(553, 100 + OBJECT_OFFSET_Y), tp(584, 110 + OBJECT_OFFSET_Y), (70, 70, 70), 2)

    # Support arm and stand
    cv2.rectangle(img, tp(564, 155 + OBJECT_OFFSET_Y), tp(571, 188 + OBJECT_OFFSET_Y), (160, 160, 160), -1)
    cv2.rectangle(img, tp(564, 155 + OBJECT_OFFSET_Y), tp(571, 188 + OBJECT_OFFSET_Y), (70, 70, 70), 2)
    cv2.rectangle(img, tp(547, 188 + OBJECT_OFFSET_Y), tp(588, 199 + OBJECT_OFFSET_Y), (170, 170, 170), -1)
    cv2.rectangle(img, tp(547, 188 + OBJECT_OFFSET_Y), tp(588, 199 + OBJECT_OFFSET_Y), (70, 70, 70), 2)


def draw_graph_area(img: np.ndarray) -> None:
    # Graph placement area: lower half center
    x1, y1, x2, y2 = 95, 184, 505, 398
    cv2.rectangle(img, tp(x1, y1), tp(x2, y2), (235, 235, 245), -1)
    cv2.rectangle(img, tp(x1, y1), tp(x2, y2), (110, 110, 110), 2)

    gx1, gy1 = tp(x1, y1)
    gx2, gy2 = tp(x2, y2)
    step = sv(30)

    # Subtle grid for layout guidance
    for x in range(gx1 + step, gx2, step):
        cv2.line(img, (x, gy1 + 1), (x, gy2 - 1), (210, 210, 220), 1)
    for y in range(gy1 + step, gy2, step):
        cv2.line(img, (gx1 + 1, y), (gx2 - 1, y), (210, 210, 220), 1)


def main() -> None:
    img = np.full((CANVAS_H, CANVAS_W, 3), 255, dtype=np.uint8)

    draw_left_reference_panel(img)
    draw_right_camera_icon(img)
    draw_graph_area(img)

    out_dir = Path("output") / "graph_assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "base_graph_template.png"
    cv2.imwrite(str(out_path), img)

    print(str(out_path))


if __name__ == "__main__":
    main()

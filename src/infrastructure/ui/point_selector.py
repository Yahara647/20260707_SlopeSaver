from typing import List, Tuple
import matplotlib.pyplot as plt
import numpy as np


class PointSelector:
    def __init__(self, img: np.ndarray) -> None:
        self.img = img
        self.points: List[Tuple[float, float]] = []
        self.fig, self.ax = plt.subplots()
        self.ax.imshow(img)

        self.cid_click = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.cid_key = self.fig.canvas.mpl_connect('key_press_event', self.on_key)

        self.scatter = None

    def onclick(self, event) -> None:
        if event.button == 1:
            if len(self.points) >= 4:
                print("すでに4点選択済みです。右クリックで削除できます。")
                return
            if event.xdata is None or event.ydata is None:
                return
            self.points.append((float(event.xdata), float(event.ydata)))
            print("Added:", self.points[-1])

        elif event.button == 3 and self.points:
            removed = self.points.pop()
            print("Removed:", removed)

        self.update_plot()

        if len(self.points) == 4:
            print("4点選択完了。Enterキーで確定できます。")

    def on_key(self, event) -> None:
        if event.key == 'enter':
            if len(self.points) == 4:
                plt.close(self.fig)
            else:
                print("4点選択されていません。")

    def update_plot(self) -> None:
        if self.scatter:
            self.scatter.remove()
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        self.scatter = self.ax.scatter(xs, ys, c='red')
        self.fig.canvas.draw()

    def select(self) -> List[Tuple[float, float]]:
        plt.show()
        return self.points

import tkinter as tk
# ★ TkAgg が Tk() を作る前に root を作って隠す（最重要）
_root = tk.Tk()
_root.withdraw()

from tkinter import ttk
from typing import List, Tuple
import numpy as np

import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "MS Gothic"

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import cv2

from domain.interfaces.i_calibration_ui import ICalibrationUI


# src/infrastructure/ui/calibration_integrated_ui.py

class CalibrationIntegratedUI(ICalibrationUI):

    def __init__(self, initial_world_points: np.ndarray | None = None) -> None:
        self.initial_world_points = initial_world_points


    def get_calibration_points(
        self,
        image: np.ndarray
    ) -> tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:

        # --- UI 初期化 ---
        self.root = tk.Toplevel()
        self.root.title("キャリブレーション（点選択 + 座標入力）")

        # ★ 追加：フォーカスを強制的に与える
        self.root.focus_force()
        self.root.grab_set()
        self.root.lift()

        self.image = image
        self.pixel_points: List[Tuple[float, float]] = []
        self.entries_xyz: List[Tuple[tk.Entry, tk.Entry, tk.Entry]] = []
        self.result = None

        # --- Matplotlib 埋め込み ---
        fig, ax = plt.subplots(figsize=(6, 6))
        img_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        ax.imshow(img_rgb)
        ax.set_title("画像をクリックして4点選択")
        ax.axis("off")

        self.ax = ax
        self.fig = fig

        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas.get_tk_widget().grid(row=0, column=0, rowspan=10)
        self.canvas = canvas

        fig.canvas.mpl_connect("button_press_event", self.on_click)

        # --- 右側の入力欄 ---
        ttk.Label(self.root, text="Point").grid(row=0, column=1)
        ttk.Label(self.root, text="X").grid(row=0, column=2)
        ttk.Label(self.root, text="Y").grid(row=0, column=3)
        ttk.Label(self.root, text="Z").grid(row=0, column=4)

        for i in range(4):
            ttk.Label(self.root, text=f"{i+1}").grid(row=i+1, column=1)

            ex = ttk.Entry(self.root, width=10)
            ey = ttk.Entry(self.root, width=10)
            ez = ttk.Entry(self.root, width=10)

            ex.grid(row=i+1, column=2)
            ey.grid(row=i+1, column=3)
            ez.grid(row=i+1, column=4)

            # ★ 初期値をセット
            if self.initial_world_points is not None and len(self.initial_world_points) > i:
                x, y, z = self.initial_world_points[i]
                ex.insert(0, str(x))
                ey.insert(0, str(y))
                ez.insert(0, str(z))

            self.entries_xyz.append((ex, ey, ez))


        ttk.Button(self.root, text="確定", command=self.on_submit).grid(
            row=10, column=1, columnspan=4
        )

        # --- UI 実行 ---
        self.root.wait_window()

        if self.result is None:
            raise RuntimeError("UI が正常に終了しませんでした")

        return self.result

    def on_submit(self) -> None:
        print("on_submit 呼ばれた。pixel_points =", len(self.pixel_points))

        if len(self.pixel_points) != 4:
            print("4点選んでください")
            return

        world_points = []
        try:
            for (ex, ey, ez) in self.entries_xyz:
                x = float(ex.get())
                y = float(ey.get())
                z = float(ez.get())
                world_points.append((x, y, z))
        except Exception as ex:
            print("入力エラー:", ex)
            return

        self.result = (self.pixel_points, world_points)

        # ★ 追加：Matplotlib のキャンバスを明示的に破棄
        self.canvas.get_tk_widget().destroy()
        self.fig.clear()

        # ★ これで destroy がブロックされなくなる
        self.root.destroy()


    def on_click(self, event) -> None:
        if event.button == 1:
            if event.xdata is None or event.ydata is None:
                return
            if len(self.pixel_points) >= 4:
                return

            x, y = event.xdata, event.ydata
            self.pixel_points.append((x, y))

            self.ax.plot(x, y, "ro")
            self.ax.text(x + 5, y + 5, str(len(self.pixel_points)), color="yellow")
            self.canvas.draw()

            idx = len(self.pixel_points) - 1
            ex, ey, ez = self.entries_xyz[idx]
            ex.configure(background="#ffffcc")
            ey.configure(background="#ffffcc")
            ez.configure(background="#ffffcc")

        elif event.button == 3:
            if len(self.pixel_points) == 0:
                return

            self.pixel_points.pop()

            idx = len(self.pixel_points)
            ex, ey, ez = self.entries_xyz[idx]
            ex.configure(background="white")
            ey.configure(background="white")
            ez.configure(background="white")

            self.ax.clear()
            img_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            self.ax.imshow(img_rgb)
            self.ax.axis("off")

            for i, (x, y) in enumerate(self.pixel_points):
                self.ax.plot(x, y, "ro")
                self.ax.text(x + 5, y + 5, str(i + 1), color="yellow")

            self.canvas.draw()

# src/infrastructure/ui/roi_setting_ui.py

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import cv2
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

plt.rcParams["font.family"] = "MS Gothic"


class RoiSettingUI:

    def __init__(self, initial_roi=None, max_w=None, max_h=None):
        """
        initial_roi: (x, y, w, h)
        max_w, max_h: カメラの最大解像度
        """
        self.initial_roi = initial_roi
        self.max_w = max_w
        self.max_h = max_h

    def get_roi(self, image: np.ndarray):
        self.root = tk.Toplevel()
        self.root.title("ROI 設定")

        self.root.focus_force()
        self.root.grab_set()
        self.root.lift()

        self.image = image
        self.result = None

        # --- Matplotlib 埋め込み ---
        fig, ax = plt.subplots(figsize=(6, 6))
        img_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        ax.imshow(img_rgb)
        ax.set_title("ROI を確認できます")
        ax.axis("off")

        self.ax = ax
        self.fig = fig

        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas.get_tk_widget().grid(row=0, column=0, rowspan=10)
        self.canvas = canvas

        # --- 右側の入力欄 ---
        ttk.Label(self.root, text="ROI 設定").grid(row=0, column=1, columnspan=3)

        # ラベル + 入力欄 + 最大値
        labels = ["x", "y", "width", "height"]
        self.entries = {}

        for i, name in enumerate(labels):
            ttk.Label(self.root, text=name).grid(row=i+1, column=1)

            entry = ttk.Entry(self.root, width=10)
            entry.grid(row=i+1, column=2)
            self.entries[name] = entry

            # 最大値表示（操作不可）
            max_val = self.max_w if name in ("x", "width") else self.max_h
            ttk.Label(self.root, text=f"max={max_val}", foreground="gray").grid(row=i+1, column=3)

        # 初期値セット
        if self.initial_roi is not None:
            x, y, w, h = self.initial_roi
            self.entries["x"].insert(0, str(x))
            self.entries["y"].insert(0, str(y))
            self.entries["width"].insert(0, str(w))
            self.entries["height"].insert(0, str(h))

        # --- ボタン ---
        ttk.Button(self.root, text="確認", command=self.on_preview).grid(row=6, column=1, columnspan=3)
        ttk.Button(self.root, text="確定", command=self.on_submit).grid(row=7, column=1, columnspan=3)

        self.root.wait_window()

        if self.result is None:
            raise RuntimeError("ROI UI が正常に終了しませんでした")

        return self.result

    # ---------------------------------------------------------
    # ★ バリデーション
    # ---------------------------------------------------------
    def validate(self, x, y, w, h) -> bool:
        if x < 0 or y < 0:
            messagebox.showerror("エラー", "x, y は 0 以上である必要があります")
            return False

        if w <= 0 or h <= 0:
            messagebox.showerror("エラー", "width, height は正の値である必要があります")
            return False

        if x + w > self.max_w:
            messagebox.showerror("エラー", f"x + width が最大値 {self.max_w} を超えています")
            return False

        if y + h > self.max_h:
            messagebox.showerror("エラー", f"y + height が最大値 {self.max_h} を超えています")
            return False

        return True

    # ---------------------------------------------------------
    # ★ 確認ボタン
    # ---------------------------------------------------------
    def on_preview(self):
        try:
            x = int(self.entries["x"].get())
            y = int(self.entries["y"].get())
            w = int(self.entries["width"].get())
            h = int(self.entries["height"].get())
        except:
            messagebox.showerror("エラー", "数値を入力してください")
            return

        if not self.validate(x, y, w, h):
            return

        # 再描画
        self.ax.clear()
        img_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.ax.imshow(img_rgb)
        self.ax.axis("off")

        rect = plt.Rectangle((x, y), w, h, fill=False, color="yellow", linewidth=2)
        self.ax.add_patch(rect)

        self.canvas.draw()

    # ---------------------------------------------------------
    # ★ 確定ボタン
    # ---------------------------------------------------------
    def on_submit(self):
        try:
            x = int(self.entries["x"].get())
            y = int(self.entries["y"].get())
            w = int(self.entries["width"].get())
            h = int(self.entries["height"].get())
        except:
            messagebox.showerror("エラー", "数値を入力してください")
            return

        if not self.validate(x, y, w, h):
            return

        self.result = (x, y, w, h)

        self.canvas.get_tk_widget().destroy()
        self.fig.clear()
        self.root.destroy()

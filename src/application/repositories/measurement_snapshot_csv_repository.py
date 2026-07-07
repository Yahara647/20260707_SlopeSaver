from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


class MeasurementSnapshotCsvRepository:
    """計測スナップショットを列指向 CSV に追記保存する Repository。"""

    MAX_PATH_LEVELS = 8
    HEADER_ROW_COUNT = 2 + MAX_PATH_LEVELS

    def __init__(self, path: str) -> None:
        self.path = Path(path)

    @staticmethod
    def _column_key(source_file: str, path_full: str) -> str:
        return f"{source_file}::{path_full}"

    @staticmethod
    def _is_legacy_vertical_format(rows: list[list[str]]) -> bool:
        if not rows:
            return False
        return len(rows[0]) > 0 and rows[0][0] == "saved_at"

    def _backup_legacy_file(self) -> None:
        suffix = self.path.suffix if self.path.suffix else ".csv"
        backup_path = self.path.with_name(self.path.stem + "_legacy" + suffix)
        idx = 1
        while backup_path.exists():
            backup_path = self.path.with_name(self.path.stem + f"_legacy_{idx}" + suffix)
            idx += 1
        self.path.rename(backup_path)

    def append_snapshot(self, entries: list[dict[str, Any]]) -> None:
        if not entries:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)

        rows: list[list[str]] = []
        if self.path.exists() and self.path.stat().st_size > 0:
            with self.path.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.reader(f))

        if self._is_legacy_vertical_format(rows):
            self._backup_legacy_file()
            rows = []

        if not rows:
            rows = [[] for _ in range(self.HEADER_ROW_COUNT)]
        else:
            while len(rows) < self.HEADER_ROW_COUNT:
                rows.append([])

        col_count = max((len(r) for r in rows), default=0)
        for r in rows:
            if len(r) < col_count:
                r.extend([""] * (col_count - len(r)))

        existing_cols: dict[str, int] = {}
        for col in range(col_count):
            source_file = rows[0][col] if col < len(rows[0]) else ""
            path_full = rows[1][col] if col < len(rows[1]) else ""
            if source_file or path_full:
                existing_cols[self._column_key(source_file, path_full)] = col

        for entry in entries:
            source_file = str(entry.get("source_file", ""))
            path_full = str(entry.get("path_full", ""))
            key = self._column_key(source_file, path_full)

            if key not in existing_cols:
                for r in rows:
                    r.append("")
                existing_cols[key] = len(rows[0]) - 1

            col = existing_cols[key]
            rows[0][col] = source_file
            rows[1][col] = path_full
            for i in range(self.MAX_PATH_LEVELS):
                rows[2 + i][col] = str(entry.get(f"path_{i + 1}", ""))

        value_row = [""] * len(rows[0])
        for entry in entries:
            source_file = str(entry.get("source_file", ""))
            path_full = str(entry.get("path_full", ""))
            key = self._column_key(source_file, path_full)
            col = existing_cols[key]
            value_row[col] = str(entry.get("value", ""))

        rows.append(value_row)

        with self.path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

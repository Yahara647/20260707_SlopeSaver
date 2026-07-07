# src/presentation/logger/application_logger.py

import logging
import logging.handlers
import os
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

# --- ログフォルダ作成 ---
ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# --- ログファイルパス ---
LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"

# --- ロガー作成 ---
logger = logging.getLogger("slope_saver")
logger.setLevel(logging.DEBUG)

# --- フォーマット ---
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] [%(threadName)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s"
)

# --- INFO 以上を app.log に書く ---

file_handler = TimedRotatingFileHandler(
    LOG_FILE,
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8"
)

file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# --- ERROR 以上を error.log に書く ---
error_handler = logging.handlers.RotatingFileHandler(
    ERROR_LOG_FILE, maxBytes=5*1024*1024, backupCount=5, encoding="utf-8"
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

# --- コンソール出力 ---
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

if not logger.handlers:
    # --- ハンドラ登録 ---
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

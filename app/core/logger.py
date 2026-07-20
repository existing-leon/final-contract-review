"""日志配置：loguru，控制台 + 文件。"""
import os
import sys

from loguru import logger

os.makedirs("logs", exist_ok=True)

logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    enqueue=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="14 days",
    level="DEBUG",
    enqueue=True,
    encoding="utf-8",
)

__all__ = ["logger"]

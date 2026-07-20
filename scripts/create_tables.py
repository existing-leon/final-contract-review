"""一键建表（dev 演示用，生产请使用 alembic 迁移）。

运行：python scripts/create_tables.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import models  # noqa: F401,E402  触发所有模型注册到 Base.metadata
from app.core.database import Base, engine  # noqa: E402


def main() -> None:
    Base.metadata.create_all(engine)
    print("✅ 表创建完成（如已存在则跳过）")


if __name__ == "__main__":
    main()

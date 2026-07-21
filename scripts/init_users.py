"""默认账号初始化数据。

运行：python scripts/init_users.py
幂等：已存在的 username 会被跳过。
默认账号：admin / admin123（系统管理员）、legal / legal123（法务审核人）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import User  # noqa: E402

# 默认账号（密码仅用于演示；生产请通过修改密码接口或环境变量覆盖）
USERS = [
    {"username": "admin", "password": "admin123", "role": "admin"},
    {"username": "legal", "password": "legal123", "role": "legal"},
]


def main() -> None:
    db = SessionLocal()
    try:
        created = 0
        for u in USERS:
            exists = db.query(User).filter(User.username == u["username"]).first()
            if exists:
                continue
            db.add(
                User(
                    username=u["username"],
                    password_hash=hash_password(u["password"]),
                    role=u["role"],
                )
            )
            created += 1
        db.commit()
        print(f"✅ 账号初始化完成：本次新增 {created} 个，总计 {len(USERS)} 个")
    finally:
        db.close()


if __name__ == "__main__":
    main()

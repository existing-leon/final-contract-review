"""pytest 公共 fixtures：sqlite 内存库 + TestClient（覆盖 get_db）。"""
import os
import sys
from collections.abc import Generator

# 将项目根加入 sys.path，使 tests 可 import app / scripts
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import models  # noqa: F401  触发模型注册
from app.core import config
from app.core.database import Base, get_db


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db(engine) -> Generator[Session, None, None]:
    SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(engine, tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    # 强制 mock 模式 + 附件写入临时目录，避免依赖真实审批系统/MySQL/磁盘
    monkeypatch.setattr(config.settings, "MOCK_APPROVAL", True, raising=False)
    monkeypatch.setattr(config.settings, "ATTACHMENT_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(config.settings, "LLM_API_KEY", "", raising=False)
    monkeypatch.setattr(config.settings, "OCR_USE_LAYOUT", False, raising=False)
    # 测试不依赖真实 PDF / pdfplumber，强制 mock 走纯文本 fallback
    import app.services.approval_client as _ac

    monkeypatch.setattr(_ac, "_ensure_sample_pdfs", lambda: [], raising=False)

    SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)

    def override_get_db() -> Generator[Session, None, None]:
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    from app.main import app

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed_rules(db: Session) -> None:
    """注入 11 条内置规则。"""
    from app.models import ReviewRule
    from scripts.init_data import RULES

    for r in RULES:
        db.add(ReviewRule(rule_status="enabled", **r))
    db.commit()

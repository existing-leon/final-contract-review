# 合同审批审查系统 - 后端

> 面向企业合同审批场景的自动审查系统：拉取审批单 → 下载附件 → 解析合同 → 规则审查 → 结果入库 → 评论回写。
> **辅助审批，不替代人工。** 默认 `MOCK_APPROVAL=True`，开箱即可演示完整闭环，无需真实审批系统。

## 技术栈

Python 3.10+ · FastAPI · Uvicorn · SQLAlchemy 2.0 · MySQL 8 · Redis · Celery · Pydantic v2 · HTTPX · pdfplumber/python-docx · RapidOCR · loguru

## 目录结构

```
app/
├── main.py              FastAPI 入口
├── core/                config/database/redis/logger/response/exceptions/constants
├── api/v1/              21 个 REST 路由
├── schemas/             Pydantic 请求/响应模型
├── models/              8 张表 ORM
├── services/            6 个服务模块（编排层）+ approval_client
├── tools/               7 个工具函数（对齐 PRD 1.3.10）
├── engine/              state_machine / rule_engine / field_extractor / parser
└── workers/             Celery 异步任务
scripts/                 init_db.sql / seed_rules.sql / create_tables.py / init_data.py
```

## 快速开始

```bash
# 1. 安装依赖
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. 配置环境
cp .env.example .env       # 演示模式默认 MOCK_APPROVAL=True，无需真实审批系统

# 3. 准备数据库（二选一）
#    a) 用 SQL：
mysql -u root -p < scripts/init_db.sql
mysql -u root -p contract_review < scripts/seed_rules.sql
#    b) 用 Python（推荐，避免正则反斜杠转义问题）：
python scripts/create_tables.py
python scripts/init_data.py

# 4. 启动
uvicorn app.main:app --reload --port 8000
# 接口文档：http://127.0.0.1:8000/docs

# 5. （可选）异步 worker
celery -A app.workers.celery_app worker -l info
```

## 完整闭环演示（mock 模式）

```bash
# 1) 拉取并去重 → 生成审批任务
curl -X POST http://127.0.0.1:8000/api/v1/tasks/pull -H "Content-Type: application/json" -d '{"limit":20}'

# 2) 任务列表，取一个 task_id
curl http://127.0.0.1:8000/api/v1/tasks

# 3) 解析合同（自动下载 mock 附件 + 解析 + 字段提取）
curl -X POST http://127.0.0.1:8000/api/v1/tasks/{task_id}/parse -H "Content-Type: application/json" -d '{"document_id":0}'

# 4) 规则审查（生成命中、风险等级、评论）
curl -X POST http://127.0.0.1:8000/api/v1/tasks/{task_id}/review -H "Content-Type: application/json" -d '{"case_id":0}'

# 5) 评论回写（mock 写回，任务流转到 done）
curl -X POST http://127.0.0.1:8000/api/v1/tasks/{task_id}/comment -H "Content-Type: application/json" -d '{"instance_id":"AP...","review_id":1}'

# 6) 查看审查结果 / 命中 / 日志
curl http://127.0.0.1:8000/api/v1/tasks/{task_id}/result
curl http://127.0.0.1:8000/api/v1/tasks/{task_id}/hits
curl http://127.0.0.1:8000/api/v1/tasks/{task_id}/logs
```

## 对接真实审批系统

1. `.env` 中将 `MOCK_APPROVAL=False`；
2. 配置 `APPROVAL_BASE_URL` 与 `APPROVAL_API_KEY`；
3. 在 `app/services/approval_client.py` 中按真实接口调整路径（`/api/external/...`）。

## 状态机

- 任务：`pending → parsing → reviewing → done`，异常 → `blocked`（可重试回到 `parsing`/`reviewing`）
- 回写：`not_written → writing → success`，失败 → `failed`（可重试）

## Docker

```bash
cp .env.example .env
docker compose up -d --build
```

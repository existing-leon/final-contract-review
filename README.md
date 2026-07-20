# 合同审批审查系统 - 后端

> 面向企业合同审批场景的自动审查系统：拉取审批单 → 下载附件 → 解析合同 → 规则审查 → 结果入库 → 评论回写。
> **辅助审批，不替代人工。** 默认 `MOCK_APPROVAL=True`，开箱即可演示完整闭环，无需真实审批系统。

## 技术栈

Python 3.10+ · FastAPI · Uvicorn · SQLAlchemy 2.0 · Alembic · MySQL 8 · Redis · Celery · Pydantic v2 · HTTPX · loguru

- **文档解析**：pdfplumber（文本型 PDF）· python-docx（Word）· PyMuPDF（扫描件 PDF 转图）
- **扫描件 OCR**：本地 PaddleOCR / RapidOCR（默认，数据不出本机）⇄ 百度智能云文字识别 API（`OCR_PROVIDER` 可切换）
- **字段提取**：LLM 优先（OpenAI 兼容：DeepSeek/通义/智谱等），正则锚点回退
- **测试/样例**：pytest · reportlab（示例 PDF 生成）

## 目录结构

```
final-contract-review/
├── app/
│   ├── main.py                 FastAPI 入口
│   ├── core/                   config/database/redis/logger/response/exceptions/constants
│   ├── api/v1/                 21 个 REST 路由
│   ├── schemas/                Pydantic 请求/响应模型
│   ├── models/                 8 张表 ORM
│   ├── services/               6 个服务模块 + approval_client
│   ├── tools/                  7 个工具函数（对齐 PRD 1.3.10）
│   ├── engine/
│   │   ├── state_machine.py    任务/回写状态机
│   │   ├── rule_engine.py      规则匹配引擎（keyword/regex/threshold/absence）
│   │   ├── field_extractor.py  正则锚点字段提取
│   │   ├── llm_extractor.py    LLM 字段提取（优先，失败回退正则）
│   │   └── parser/
│   │       ├── __init__.py     parse_file 按类型路由
│   │       ├── pdf_parser.py   文本层 + 扫描件分支
│   │       ├── docx_parser.py
│   │       ├── ocr_parser.py   OCR provider 路由（local/baidu_api）
│   │       ├── baidu_ocr.py    百度智能云文字识别客户端
│   │       └── pdf_to_image.py PyMuPDF 转图
│   └── workers/                Celery 异步任务
├── alembic/                    数据库迁移（0001 初始 = 8 表）
├── scripts/                    init_db / seed_rules / create_tables / init_data
│                               make_sample_pdf / run_demo_local / test_llm / test_ocr
├── tests/                      pytest（状态机/规则引擎/字段提取/API e2e）
├── postman/                    Postman 集合 + httpie 脚本
├── samples/                    示例合同（由 make_sample_pdf 生成）
├── storage/                    附件本地存储
├── requirements.txt / requirements-dev.txt
├── .env.example / Dockerfile / docker-compose.yml
```

## 快速开始

```bash
# 1. 安装依赖
python -m venv .venv && source .venv/Scripts/activate    # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt            # 测试 / PDF 生成（可选）

# 2. 配置
cp .env.example .env        # 默认 MOCK_APPROVAL=True，无需真实审批系统

# 3. 数据库（三选一）
python scripts/create_tables.py && python scripts/init_data.py   # ✅ 推荐（建表 + 11 条规则）
# alembic upgrade head && python scripts/init_data.py            # Alembic 迁移
# mysql -u root -p < scripts/init_db.sql                         # 纯 SQL（再导入 seed_rules.sql）

# 4. 启动
uvicorn app.main:app --reload --port 8000      # http://127.0.0.1:8000/docs

# 5.（可选）异步 worker
celery -A app.workers.celery_app worker -l info

# 6.（可选）测试
python -m pytest -v
```

## OCR 配置（核心：本地 ⇄ 云端可切换）

| `OCR_PROVIDER` | 实现 | 数据安全 |
| --- | --- | --- |
| `local`（默认） | 本地 PaddleOCR + PP-Structure（版面分析/表格还原），RapidOCR 兜底 | ✅ 数据不出本机，推荐生产 |
| `baidu_api` | 百度智能云文字识别 API（通用文字识别 + 表格识别） | ⚠️ 图片上传百度云，作为自部署前的过渡 |

```dotenv
# .env：切换到百度云 API
OCR_PROVIDER=baidu_api
BAIDU_OCR_API_KEY=你的AK
BAIDU_OCR_SECRET_KEY=你的SK
# 扫描件 PDF 转图依赖：pip install pymupdf
```

- 文本型 PDF 始终走 pdfplumber（不变）；
- 扫描件 PDF：PyMuPDF 转图 → 按 `OCR_PROVIDER` 走 OCR；
- 自部署模型就绪后，把 `OCR_PROVIDER` 改回 `local` 即可，**业务代码无感切换**。

## LLM 字段提取配置（可选，增强鲁棒性）

```dotenv
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=deepseek-v4-flash
LLM_TIMEOUT=60
LLM_TRUST_ENV=False     # False=忽略系统/环境代理直连（国内服务推荐）
LLM_MAX_RETRIES=3       # 调用失败自动重试
```

- 留空则走正则锚点提取；
- LLM 调用失败自动回退正则，不阻断流程；
- 条款结构含 `exists / content / key_params`，基本信息与条款均输出统一字段对象。

## 完整闭环演示（mock 模式）

```bash
# 1) 拉取并去重 → 生成审批任务
curl -X POST http://127.0.0.1:8000/api/v1/tasks/pull -H "Content-Type: application/json" -d '{"limit":20}'
# 2) 任务列表，取一个 task_id
curl http://127.0.0.1:8000/api/v1/tasks
# 3) 解析合同（自动下载 mock 真实 PDF + LLM/正则字段提取）
curl -X POST http://127.0.0.1:8000/api/v1/tasks/{task_id}/parse -H "Content-Type: application/json" -d '{"document_id":0}'
# 4) 规则审查（命中、风险等级、回写评论）
curl -X POST http://127.0.0.1:8000/api/v1/tasks/{task_id}/review -H "Content-Type: application/json" -d '{"case_id":0}'
# 5) 评论回写（任务流转到 done）
curl -X POST http://127.0.0.1:8000/api/v1/tasks/{task_id}/comment -H "Content-Type: application/json" -d '{"instance_id":"AP...","review_id":1}'
# 6) 查看结果 / 命中 / 日志
curl http://127.0.0.1:8000/api/v1/tasks/{task_id}/result
curl http://127.0.0.1:8000/api/v1/tasks/{task_id}/hits
curl http://127.0.0.1:8000/api/v1/tasks/{task_id}/logs   # 含 OCR provider 审计
```

## 联调与自检

- **Postman**：导入 `postman/合同审批审查系统.postman_collection.json`（21 接口 + 变量自动串联闭环）
- **httpie**：`bash postman/httpie_demo.sh`
- **本地 PDF 演示**（不经 API）：`python scripts/make_sample_pdf.py && python scripts/run_demo_local.py`
- **LLM 抽取自检**：`python scripts/test_llm.py`
- **OCR 自检**：`python scripts/test_ocr.py 你的扫描件.pdf`

## 对接真实审批系统

1. `.env` 中 `MOCK_APPROVAL=False`；
2. 配置 `APPROVAL_BASE_URL` 与 `APPROVAL_API_KEY`；
3. 在 `app/services/approval_client.py` 调整 `/api/external/...` 路径。

## 状态机

- 任务：`pending → parsing → reviewing → done`，异常 → `blocked`（可重试回到 `parsing`/`reviewing`）
- 回写：`not_written → writing → success`，失败 → `failed`（可重试）

## 数据安全与审计

- **本地 OCR（默认）**：合同图片不出服务器，适合敏感商业数据；
- **百度云 OCR（过渡）**：图片上传百度云，建议自部署模型后切回 `local`；
- **审计**：每次解析在 `task_logs` 记录 `OCR 审计: provider=... source=... pages=...`，可在前端日志页或 `GET /tasks/{id}/logs` 回溯。

## Docker

```bash
cp .env.example .env
docker compose up -d --build
```

# 联调集合（Postman / httpie）

本目录提供两套联调工具，覆盖后端全部 21 个接口。

## 文件

| 文件 | 说明 |
| --- | --- |
| `合同审批审查系统.postman_collection.json` | Postman Collection v2.1，可直接导入 Postman |
| `httpie_demo.sh` | httpie 闭环脚本（bash），带 jq 自动提取 id |

## 一、Postman

### 导入

Postman → Import → 选择 `合同审批审查系统.postman_collection.json`。

### 内置变量（Collection Variables）

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `base_url` | `http://127.0.0.1:8000/api/v1` | 后端地址，按需修改 |
| `task_id` | `1` | 任务 ID |
| `approval_code` / `instance_id` | `AP20260720001` | 审批编号 |
| `attachment_id` | `A1` | 附件编号 |
| `review_id` | `1` | 审查结果 ID |
| `rule_id` | `1` | 规则 ID |

### 闭环演示（按顺序点击即可，变量自动串联）

「任务列表」「查询审查结果」两个请求内置了 **Tests 脚本**，会自动把返回的 `id` / `approval_code` 写回集合变量，后续请求无需手动填。

1. **任务 → 拉取并去重**
2. **任务 → 任务列表**（自动写入 `task_id` / `approval_code`）
3. **解析 → 解析合同**
4. **规则审查与结果 → 规则审查**
5. **规则审查与结果 → 查询审查结果**（自动写入 `review_id`）
6. **规则审查与结果 → 评论回写**（任务流转到 `done`）

> 评论回写请求体里的 `review_id` 若想用变量，可把 raw 中的 `1` 改为 `{{review_id}}`。

## 二、httpie

依赖：`httpie`（`pip install httpie`），可选 `jq`（用于自动提取 id）。

```bash
# 默认连本地 8000
bash postman/httpie_demo.sh

# 指定后端地址
BASE_URL=http://10.0.0.1:8000/api/v1 bash postman/httpie_demo.sh
```

脚本按 1)~12) 顺序跑完整闭环：拉取 → 任务列表（提取 task_id/approval_code）→ 审批详情 → 附件 → 解析 → 规则审查 → 命中 → 审查结果（提取 review_id）→ 评论回写 → 任务详情/日志 → 规则管理。

> 未安装 `jq` 时，脚本会在需要处提示手动粘贴 id。

## 接口分组速查（共 21 个）

| 分组 | 接口 |
| --- | --- |
| 待办与审批 | `GET /approvals/pending`、`GET /approvals/{instance_id}` |
| 任务 | `POST /tasks/pull`、`GET /tasks`、`GET /tasks/{id}`、`POST /tasks/{id}/retry` |
| 附件 | `GET /tasks/{id}/attachments`、`POST /tasks/{id}/attachments/{aid}/download`、`GET /attachments/{id}/file` |
| 解析 | `POST /tasks/{id}/parse`、`GET /tasks/{id}/parse` |
| 规则审查与结果 | `POST /tasks/{id}/review`、`GET /tasks/{id}/hits`、`GET /tasks/{id}/result`、`POST /tasks/{id}/result`、`POST /tasks/{id}/comment` |
| 日志 | `GET /tasks/{id}/logs` |
| 规则管理 | `GET /rules`、`POST /rules`、`PUT /rules/{id}`、`PATCH /rules/{id}/status` |

## 前置条件

- 后端已启动（`uvicorn app.main:app --port 8000`）；
- 数据库已建表 + 规则已初始化（`python scripts/create_tables.py && python scripts/init_data.py`，或 `alembic upgrade head`）；
- 默认 `MOCK_APPROVAL=True`，无需真实审批系统即可跑通闭环。

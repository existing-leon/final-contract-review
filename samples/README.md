# 示例合同（samples/）

本目录存放用于演示**真实 PDF 解析**的合同样本（由脚本生成，非 mock 文本）。

## 三份示例覆盖的场景

| 文件 | 场景 | 预期命中规则 |
| --- | --- | --- |
| `正常采购合同.pdf` | 低风险，条款齐全、条件合理 | 几乎不命中，总风险「低」 |
| `高风险采购合同.pdf` | 高预付款、长账期、自动续约、对方管辖、缺失多类条款 | 预付款/付款周期/自动续约/管辖/违约 + 保密·数据·知识产权·验收缺失，总风险「高」 |
| `简易合同.pdf` | 主体与金额缺失 | 主体缺失/金额缺失 + 预付款/付款周期，总风险「高」 |

## 1. 生成 PDF

依赖 `reportlab`（使用内置 `STSong-Light` CJK 字体，pdfplumber 可正常提取中文）：

```bash
pip install reportlab
python scripts/make_sample_pdf.py
```

## 2. 本地闭环演示（不依赖 MySQL / 审批系统）

依赖 `pdfplumber`。该脚本直接对 `samples/*.pdf` 跑 **解析 → 字段提取 → 规则匹配**，打印命中结论：

```bash
pip install pdfplumber
python scripts/run_demo_local.py
```

> 规则取自 `scripts/init_data.py` 的内置 `RULES`（11 条），无需连接数据库。

## 3. 通过完整 API 服务演示（已自动接入真实 PDF）

mock 模式（`MOCK_APPROVAL=True`）下，`app/services/approval_client.py` 的 `_mock_attachment_bytes` 会**自动读取 `samples/` 下的真实 PDF** 作为审批附件返回（按审批单 `instance_id` 确定性选一份，同一审批单每次拿到同一份）。

完整闭环：拉取任务 → 解析合同（自动下载真实 PDF → pdfplumber 解析 → 字段提取）→ 规则审查 → 评论回写。

```bash
# 1) 生成示例 PDF（需 reportlab）
python scripts/make_sample_pdf.py

# 2) 启动后端（需 pdfplumber 解析 PDF）
uvicorn app.main:app --reload

# 3) 调解析接口，即可看到真实 PDF 的解析结果
curl -X POST http://127.0.0.1:8000/api/v1/tasks/{task_id}/parse \
     -H "Content-Type: application/json" -d '{"document_id":0}'
```

> 若 `samples/` 下无 PDF 且未安装 reportlab，mock 会自动回退为内置纯文本（仍可演示闭环，但走文本解析器）。下载工具按内容 magic bytes 自动判定后缀（PDF→`.pdf`，文本→`.txt`），无需手动指定。

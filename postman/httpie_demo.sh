#!/usr/bin/env bash
# 合同审批审查系统 - httpie 联调脚本
# 依赖：httpie（pip install httpie）、jq（可选，用于自动提取 id 串联闭环）
#
# 用法：
#   bash postman/httpie_demo.sh
#   BASE_URL=http://10.0.0.1:8000/api/v1 bash postman/httpie_demo.sh
set -euo pipefail

BASE="${BASE_URL:-http://127.0.0.1:8000/api/v1}"
HAS_JQ="$(command -v jq >/dev/null 2>&1 && echo yes || echo no)"

line() { printf '\n========== %s ==========\n' "$1"; }

line "1) 拉取并去重"
http --check-status POST "$BASE/tasks/pull" limit:=20

line "2) 任务列表"
http "$BASE/tasks"
if [ "$HAS_JQ" = "yes" ]; then
  TASK_ID=$(http "$BASE/tasks" | jq -r '.data.items[0].id')
  APPROVAL_CODE=$(http "$BASE/tasks" | jq -r '.data.items[0].approval_code')
  echo ">> 自动提取 TASK_ID=$TASK_ID  APPROVAL_CODE=$APPROVAL_CODE"
else
  read -r -p "请从上方任务列表复制 TASK_ID: " TASK_ID
  read -r -p "请复制对应 APPROVAL_CODE: " APPROVAL_CODE
fi

line "3) 审批详情"
http "$BASE/approvals/$APPROVAL_CODE"

line "4) 附件列表"
http "$BASE/tasks/$TASK_ID/attachments"

line "5) 解析合同（自动下载真实 PDF/mock 附件并提取字段）"
http --check-status POST "$BASE/tasks/$TASK_ID/parse" document_id:=0

line "6) 查询解析结果"
http "$BASE/tasks/$TASK_ID/parse"

line "7) 规则审查（生成命中、风险等级、回写评论）"
http --check-status POST "$BASE/tasks/$TASK_ID/review" case_id:=$TASK_ID

line "8) 命中列表"
http "$BASE/tasks/$TASK_ID/hits"

line "9) 查询审查结果"
http "$BASE/tasks/$TASK_ID/result"
if [ "$HAS_JQ" = "yes" ]; then
  REVIEW_ID=$(http "$BASE/tasks/$TASK_ID/result" | jq -r '.data.id')
  echo ">> 自动提取 REVIEW_ID=$REVIEW_ID"
else
  read -r -p "请从上方审查结果复制 REVIEW_ID: " REVIEW_ID
fi

line "10) 评论回写（任务流转到 done）"
http --check-status POST "$BASE/tasks/$TASK_ID/comment" \
  instance_id="$APPROVAL_CODE" review_id:=$REVIEW_ID

line "11) 任务详情 / 日志（确认 done + 回写 success）"
http "$BASE/tasks/$TASK_ID"
http "$BASE/tasks/$TASK_ID/logs"

line "12) 规则管理"
http "$BASE/rules"

echo
echo "✅ 闭环完成。"

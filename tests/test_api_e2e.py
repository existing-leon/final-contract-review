"""API 端到端闭环测试（mock 模式 + sqlite）。

覆盖：拉取去重 → 任务列表 → 解析 → 规则审查 → 结果保存 → 评论回写。
"""


def test_full_closed_loop(client, seed_rules):
    # 1) 拉取并去重
    r = client.post("/api/v1/tasks/pull", json={"limit": 20})
    assert r.status_code == 200
    pull = r.json()["data"]
    assert pull["created"] > 0

    # 2) 任务列表
    r = client.get("/api/v1/tasks")
    tasks = r.json()["data"]["items"]
    assert tasks
    task = tasks[0]
    task_id = task["id"]
    approval_code = task["approval_code"]

    # 3) 解析合同（自动下载 mock 附件 + 字段提取）
    r = client.post(f"/api/v1/tasks/{task_id}/parse", json={"document_id": 0})
    assert r.status_code == 200
    parsed = r.json()["data"]
    assert parsed["parse_status"] == "success"
    assert parsed["basic_info"]["contract_no"]["value"].startswith("HT-")

    # 4) 规则审查
    r = client.post(f"/api/v1/tasks/{task_id}/review", json={"case_id": task_id})
    assert r.status_code == 200
    conclusion = r.json()["data"]
    assert len(conclusion["hits"]) > 0
    assert conclusion["overall_risk_level"] in ("low", "medium", "high")
    assert conclusion["comment_text"]

    # 5) 取审查结果拿到 review_id
    r = client.get(f"/api/v1/tasks/{task_id}/result")
    assert r.status_code == 200
    review_id = r.json()["data"]["id"]

    # 6) 评论回写
    r = client.post(
        f"/api/v1/tasks/{task_id}/comment",
        json={"instance_id": approval_code, "review_id": review_id},
    )
    assert r.status_code == 200
    assert r.json()["data"]["write_status"] == "success"

    # 任务流转到 done
    r = client.get(f"/api/v1/tasks/{task_id}")
    assert r.json()["data"]["task_status"] == "done"
    assert r.json()["data"]["write_status"] == "success"


def test_dedupe_on_second_pull(client, seed_rules):
    client.post("/api/v1/tasks/pull", json={"limit": 20})
    r2 = client.post("/api/v1/tasks/pull", json={"limit": 20})
    # 第二次拉取应全部命中已有记录：created=0
    assert r2.json()["data"]["created"] == 0


def test_retry_only_for_blocked(client, seed_rules):
    client.post("/api/v1/tasks/pull", json={"limit": 5})
    task_id = client.get("/api/v1/tasks").json()["data"]["items"][0]["id"]
    # pending 状态不允许重试
    r = client.post(f"/api/v1/tasks/{task_id}/retry", json={})
    assert r.status_code != 200 or r.json()["code"] != 0

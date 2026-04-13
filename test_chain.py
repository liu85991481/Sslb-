#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSLB 三层链路测试: 中书省 → 尚书省 → 工部
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime

ROOT = Path("D:/sslb")

AGENTS = {
    "zhongshusheng": "ZHONG_SHU_SHENG_PROMPT",
    "shangshusheng": "SHANG_SHU_SHENG_PROMPT",
    "gongbu": "GONG_BU_PROMPT",
}

API_BASE = "https://api.svips.org"
API_KEY = "sk-510defdaa8231977542f69248b2e5477ff49750b7a31e1a5d7a5f63cd1bbda7b"
MODEL = "MiniMax-M2.7"

def call_api(prompt: str) -> str:
    import requests
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 2000, "temperature": 0.7}
    resp = requests.post(f"{API_BASE}/v1/chat/completions", headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def create_task(agent_id: str, content: str, prev_result: str = None):
    task_id = f"chain_{datetime.now().strftime('%H%M%S')}"
    task = {
        "task_id": task_id,
        "from": "human",
        "to": agent_id,
        "content": content,
        "priority": "high",
        "timestamp": datetime.now().isoformat()
    }
    if prev_result:
        task["prev_result"] = prev_result
    inbox = ROOT / agent_id / "inbox"
    inbox.mkdir(exist_ok=True)
    fpath = inbox / f"{task_id}.json"
    fpath.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
    return task_id, task

def save_result(agent_id: str, task_id: str, raw: str):
    outbox = ROOT / agent_id / "outbox"
    outbox.mkdir(exist_ok=True)
    result = {
        "task_id": task_id,
        "from": agent_id,
        "status": "done",
        "raw": raw[:2000]
    }
    result_file = outbox / f"result_{task_id}.json"
    result_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    raw_file = outbox / f"{task_id}_raw.txt"
    raw_file.write_text(raw, encoding="utf-8")
    return result_file

def test_agent(agent_id: str, task_content: str, prev_result: str = None):
    sys.path.insert(0, str(ROOT / "my_agent_project"))
    from importlib import import_module
    prompts = import_module("prompts")
    prompt_var = AGENTS[agent_id]
    prompt_template = getattr(prompts, prompt_var)

    task_id, task = create_task(agent_id, task_content, prev_result)
    prompt = f"{prompt_template}\n\n## Task\n{json.dumps(task, ensure_ascii=False, indent=2)}\n"

    print(f"  [{agent_id}] Task: {task_id}")
    raw = call_api(prompt)
    result_file = save_result(agent_id, task_id, raw)
    print(f"  [{agent_id}] Result saved: {result_file.name}")
    return raw

def main():
    print("=" * 60)
    print("SSLB 三层链路测试: 中书省 → 尚书省 → 工部")
    print("=" * 60)

    # 第一层：中书省
    print("\n[第一层] 中书省 - 制定方案")
    task = "开发一个用户登录系统"
    zhong_result = test_agent("zhongshusheng", task)
    print(f"  [中书省] 输出长度: {len(zhong_result)} 字符")

    # 第二层：尚书省
    print("\n[第二层] 尚书省 - 分发任务")
    shang_result = test_agent("shangshusheng", task, zhong_result[:1500])
    print(f"  [尚书省] 输出长度: {len(shang_result)} 字符")

    # 第三层：工部
    print("\n[第三层] 工部 - 技术执行")
    gong_result = test_agent("gongbu", task, shang_result[:1500])
    print(f"  [工部] 输出长度: {len(gong_result)} 字符")

    print("\n" + "=" * 60)
    print("三层链路测试完成!")
    print("=" * 60)

    # 显示输出摘要
    print("\n=== 输出摘要 ===")
    print(f"\n[中书省] {zhong_result[:300]}...")
    print(f"\n[尚书省] {shang_result[:300]}...")
    print(f"\n[工部] {gong_result[:300]}...")

if __name__ == "__main__":
    main()

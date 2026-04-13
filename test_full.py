#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSLB 全流程测试脚本
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime

ROOT = Path("D:/sslb")

AGENTS = {
    "zhongshusheng": "ZHONG_SHU_SHENG_PROMPT",
    "menxiasheng": "MEN_XIA_SHENG_PROMPT",
    "shangshusheng": "SHANG_SHU_SHENG_PROMPT",
    "libu": "LI_BU_PROMPT",
    "hubu": "HU_BU_PROMPT",
    "liyibu": "LI_YI_BU_PROMPT",
    "bingbu": "BING_BU_PROMPT",
    "xingbu": "XING_BU_PROMPT",
    "gongbu": "GONG_BU_PROMPT",
}

API_BASE = "https://api.svips.org"
API_KEY = "sk-510defdaa8231977542f69248b2e5477ff49750b7a31e1a5d7a5f63cd1bbda7b"
MODEL = "MiniMax-M2.7"

def create_task(agent_id: str, content: str):
    task_id = f"test_{datetime.now().strftime('%H%M%S')}"
    task = {
        "task_id": task_id,
        "from": "human",
        "to": agent_id,
        "content": content,
        "priority": "high",
        "timestamp": datetime.now().isoformat()
    }
    inbox = ROOT / agent_id / "inbox"
    inbox.mkdir(exist_ok=True)
    fpath = inbox / f"{task_id}.json"
    fpath.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
    return task_id, task

def call_api(prompt: str) -> str:
    import requests
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 2000, "temperature": 0.7}
    resp = requests.post(f"{API_BASE}/v1/chat/completions", headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def extract_json(raw: str) -> dict:
    m = re.search(r'\{[\s\S]+\}', raw)
    if m:
        try:
            return json.loads(m.group())
        except:
            pass
    return {"raw": raw[:500]}

def save_result(agent_id: str, task_id: str, result: dict, raw: str):
    outbox = ROOT / agent_id / "outbox"
    outbox.mkdir(exist_ok=True)
    result_file = outbox / f"result_{task_id}.json"
    result["task_id"] = task_id
    result["from"] = agent_id
    result["status"] = "done"
    result_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    raw_file = outbox / f"{task_id}_raw.txt"
    raw_file.write_text(raw, encoding="utf-8")
    return result_file

def test_agent(agent_id: str, test_content: str = "你是谁") -> dict:
    prompt_var = AGENTS.get(agent_id)
    if not prompt_var:
        return {"error": f"Unknown agent: {agent_id}"}

    sys.path.insert(0, str(ROOT / "my_agent_project"))
    from importlib import import_module
    prompts = import_module("prompts")
    prompt_template = getattr(prompts, prompt_var, None)
    if not prompt_template:
        return {"error": f"Prompt not found: {prompt_var}"}

    task_id, task = create_task(agent_id, test_content)
    prompt = f"{prompt_template}\n\n## Task\n{json.dumps(task, ensure_ascii=False)}\n"

    try:
        raw = call_api(prompt)
        result = extract_json(raw)
        result_file = save_result(agent_id, task_id, result, raw)
        return {
            "task_id": task_id,
            "status": "success",
            "agent": agent_id,
            "result_file": str(result_file),
            "raw_length": len(raw),
            "response": raw[:600]
        }
    except Exception as e:
        return {"task_id": task_id, "status": "error", "agent": agent_id, "error": str(e)}

def test_all(test_content: str = "你是谁") -> dict:
    results = {}
    for agent_id in AGENTS.keys():
        print(f"Testing {agent_id}...", end=" ")
        result = test_agent(agent_id, test_content)
        results[agent_id] = result
        if result.get("status") == "success":
            print("OK")
        else:
            print(f"ERROR: {result.get('error', 'unknown')}")
    return results

if __name__ == "__main__":
    print("=" * 60)
    print("SSLB 全部门测试")
    print("=" * 60)
    results = test_all("你是谁")
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for agent, r in results.items():
        status = r.get("status", "unknown")
        task_id = r.get("task_id", "-")
        print(f"{agent:15} [{status:7}] {task_id}")

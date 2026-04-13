#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSLB 多智能体调度器
功能：监听各智能体 outbox，路由消息，启动对应 .bat
"""

import json
import time
import subprocess
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# ─────────────── 路径配置 ───────────────
ROOT = Path("D:/sslb")
BUS  = ROOT / ".bus"
LOGS = BUS / "logs"

# ─────────────── 智能体 bat 文件路径 ───────────────
BAT_FILES = {
    "zhongshusheng": ROOT / "zhongshusheng" / "start-claude.bat",
    "menxiasheng":   ROOT / "menxiasheng"   / "start-claude.bat",
    "shangshusheng": ROOT / "shangshusheng" / "start-claude.bat",
    "libu":          ROOT / "libu"          / "start-claude.bat",
    "hubu":          ROOT / "hubu"          / "start-claude.bat",
    "liyibu":        ROOT / "liyibu"        / "start-claude.bat",
    "bingbu":        ROOT / "bingbu"        / "start-claude.bat",
    "xingbu":        ROOT / "xingbu"        / "start-claude.bat",
    "gongbu":        ROOT / "gongbu"        / "start-claude.bat",
}

# ─────────────── 上级路由表 ───────────────
SUPERIORS = {
    "menxiasheng":   "zhongshusheng",
    "shangshusheng": "zhongshusheng",
    "libu":          "shangshusheng",
    "hubu":          "shangshusheng",
    "liyibu":        "shangshusheng",
    "bingbu":        "shangshusheng",
    "xingbu":        "shangshusheng",
    "gongbu":        "shangshusheng",
}

def log(agent: str, msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{agent:>14}] {msg}")

def write_inbox(to_agent: str, message: dict):
    """向目标智能体的 inbox 写入任务 JSON"""
    inbox = ROOT / to_agent / "inbox"
    inbox.mkdir(exist_ok=True)
    task_id = message.get("task_id", f"task_{int(time.time())}")
    fpath = inbox / f"{task_id}.json"
    fpath.write_text(json.dumps(message, ensure_ascii=False, indent=2), encoding="utf-8")
    log("dispatcher", f"📤 消息写入 {to_agent}/inbox/{task_id}.json")
    return fpath

def archive_message(agent: str, fpath: Path):
    archive = BUS / "archive" / agent
    archive.mkdir(parents=True, exist_ok=True)
    dest = archive / fpath.name
    shutil.move(str(fpath), str(dest))

def start_agent(agent_id: str, task_file: Path):
    """启动对应智能体的 bat 文件"""
    bat = BAT_FILES.get(agent_id)
    if not bat or not bat.exists():
        log("dispatcher", f"WARNING 未找到 {agent_id} 的 bat 文件")
        return
    log("dispatcher", f"🚀 唤醒 [{agent_id}]，任务: {task_file.name}")
    env = {"TASK_FILE": str(task_file), "AGENT_ID": agent_id}
    subprocess.Popen(
        [str(bat)],
        shell=True,
        env={**__import__("os").environ, **env}
    )

def update_status(agent: str, status: str, task_id: str = ''):
    status_file = ROOT / agent / ".status"
    data = {
        "status": status,
        "agent": agent,
        "task_id": task_id,
        "updated_at": datetime.now().isoformat()
    }
    status_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

def process_outbox(agent: str):
    """检查智能体 outbox，处理完成的结果"""
    outbox = ROOT / agent / "outbox"
    if not outbox.exists():
        return
    for result_file in outbox.glob("*.json"):
        try:
            data = json.loads(result_file.read_text(encoding="utf-8"))
            task_id = data.get("task_id", result_file.stem)
            status  = data.get("status", "unknown")
            log(agent, f"📥 收到结果: {task_id} 状态={status}")
            # 写入全局日志
            log_file = LOGS / f"{datetime.now().strftime('%Y%m%d')}_{agent}.jsonl"
            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps({**data, "_received_at": datetime.now().isoformat()}, ensure_ascii=False) + "\n")
            # 上报结果给上级
            superior = SUPERIORS.get(agent)
            if superior and status == "done":
                report_msg = {
                    "task_id":   task_id,
                    "from":      agent,
                    "to":        superior,
                    "type":      "result",
                    "status":    "done",
                    "summary":   data.get("summary", "任务完成"),
                    "artifacts": data.get("artifacts", []),
                    "timestamp": datetime.now().isoformat(),
                }
                new_file = write_inbox(superior, report_msg)
                log(agent, f"↑ 结果已上报至 [{superior}]")
                start_agent(superior, new_file)
            update_status(agent, "idle")
            archive_message(agent, result_file)
        except Exception as e:
            log(agent, f"ERROR 处理结果失败: {e}")

def dispatch_command(from_agent, to_agent, command, priority='normal'):
    """主动分发命令"""
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    message = {
        "task_id":   task_id,
        "from":      from_agent,
        "to":        to_agent,
        "type":      "command",
        "priority":  priority,
        "content":   command,
        "timestamp": datetime.now().isoformat(),
    }
    task_file = write_inbox(to_agent, message)
    update_status(to_agent, 'busy', task_id)
    start_agent(to_agent, task_file)
    return task_id

def run_orchestrator():
    print("SSLB 多智能体调度器 已启动")
    log("dispatcher", "开始监听所有智能体 outbox（每秒轮询）...")
    agents = list(BAT_FILES.keys())
    while True:
        for agent in agents:
            process_outbox(agent)
        time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["orchestrator","send"], default="orchestrator")
    parser.add_argument("--from-agent", default="human")
    parser.add_argument("--to-agent",   default="zhongshusheng")
    parser.add_argument("--command",    default="执行测试任务")
    args = parser.parse_args()
    LOGS.mkdir(parents=True, exist_ok=True)
    if args.mode == "orchestrator":
        run_orchestrator()
    elif args.mode == "send":
        dispatch_command(args.from_agent, args.to_agent, args.command)

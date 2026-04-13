#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSLB 多智能体系统 - 实时状态监控
python monitor.py
"""
import json
import time
import os
from pathlib import Path

ROOT = Path("D:/sslb")
AGENTS = [
    "zhongshusheng", "menxiasheng", "shangshusheng",
    "libu", "hubu", "liyibu", "bingbu", "xingbu", "gongbu"
]
ICONS = {"idle": "OK", "busy": "BUSY", "error": "ERR", "unknown": "WAIT"}

def read_status(agent):
    f = ROOT / agent / ".status"
    if not f.exists():
        return {"status": "unknown", "task_id": ""}
    try:
        return json.loads(f.read_text("utf-8"))
    except:
        return {"status": "unknown"}

def count_files(agent, folder):
    d = ROOT / agent / folder
    if not d.exists():
        return 0
    return len(list(d.glob("*.json")))

def main():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("=" * 60)
        print("  SSLB 多智能体系统 - 实时状态监控")
        print("=" * 60)
        print(f"  更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        print(f"  {'智能体':<16} {'状态':<8} {'任务ID':<20} {'inbox':>5} {'outbox':>5}")
        print("-" * 60)

        for agent in AGENTS:
            s = read_status(agent)
            status = s.get("status", "unknown")
            task = s.get("task_id", "")[:18]
            icon = ICONS.get(status, "?")
            inbox = count_files(agent, "inbox")
            outbox = count_files(agent, "outbox")
            print(f"  {agent:<16} [{icon}]  {status:<8} {task:<20} {inbox:>5} {outbox:>5}")

        print("-" * 60)
        print("  按 Ctrl+C 退出")
        print("=" * 60)
        time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n监控已退出")

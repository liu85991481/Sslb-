#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSLB 测试脚本 - 手动测试单个智能体
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, 'D:/sslb/my_agent_project')
from prompts import ZHONG_SHU_SHENG_PROMPT

ROOT = Path('D:/sslb')

def create_test_task():
    """创建测试任务"""
    task_id = f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    inbox = ROOT / 'zhongshusheng' / 'inbox'
    inbox.mkdir(parents=True, exist_ok=True)

    task = {
        'task_id': task_id,
        'from': 'human',
        'to': 'zhongshusheng',
        'type': 'command',
        'content': '开发一个用户登录系统，包含用户名密码验证',
        'timestamp': datetime.now().isoformat(),
        'priority': 'high'
    }

    fpath = inbox / f'{task_id}.json'
    fpath.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding='utf-8')
    return task_id, fpath

def build_prompt(agent_id: str, task: dict) -> str:
    """构建提示词"""
    prompts = {
        'zhongshusheng': ZHONG_SHU_SHENG_PROMPT,
    }
    system = prompts.get(agent_id, f'你是{agent_id}智能体')
    return f'''{system}

## 当前任务
```json
{json.dumps(task, ensure_ascii=False, indent=2)}
```
请严格按输出格式处理。'''

if __name__ == '__main__':
    print('=== SSLB 测试脚本 ===')

    # 1. 创建测试任务
    task_id, fpath = create_test_task()
    print(f'[OK] 测试任务已创建: {fpath}')

    # 2. 读取任务
    task = json.loads(fpath.read_text(encoding='utf-8'))
    print(f'[OK] 任务内容: {task["content"]}')

    # 3. 构建提示词
    prompt = build_prompt('zhongshusheng', task)
    print(f'[OK] 提示词已生成，长度: {len(prompt)} 字符')

    # 4. 保存提示词到文件
    prompt_file = fpath.parent / f'_prompt_{task_id}.txt'
    prompt_file.write_text(prompt, encoding='utf-8')
    print(f'[OK] 提示词已保存: {prompt_file}')

    print()
    print('=== 下一步 ===')
    print('1. 手动运行: D:\\sslb\\zhongshusheng\\start-claude.bat')
    print('2. 或运行: python D:\\sslb\\my_agent_project\\dispatcher.py')
    print()

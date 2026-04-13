#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 raw 输出中提取 JSON 结果
"""
import sys
import json
import re
from pathlib import Path

def extract_result(raw_file: str, result_file: str, task_id: str, agent_id: str):
    raw_path = Path(raw_file)
    result_path = Path(result_file)

    if not raw_path.exists():
        print(f'WARN: Raw file not found: {raw_file}')
        return False

    raw = raw_path.read_text('utf-8', errors='ignore')

    # Try to find and parse JSON
    result = {'task_id': task_id, 'from': agent_id, 'status': 'done'}

    m = re.search(r'\{[\s\S]+\}', raw)
    if m:
        try:
            parsed = json.loads(m.group())
            result.update(parsed)
            result['task_id'] = task_id
            result['from'] = agent_id
        except:
            result['summary'] = raw[:500]
    else:
        result['summary'] = raw[:500]

    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    print(f'OK: Result saved to {result_path}')
    return True

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print('Usage: extract_result.py <raw_file> <result_file> <task_id> <agent_id>')
        sys.exit(1)

    extract_result(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

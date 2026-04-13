@echo off
chcp 65001 >nul
REM ═══════════════════════════════════════
REM  SSLB 智能体启动脚本 (Qwen API 版)
REM  适用于: gongbu
REM ═══════════════════════════════════════

SET AGENT_ID=gongbu
SET AGENT_DIR=D:\sslb\%AGENT_ID%
SET INBOX=%AGENT_DIR%\inbox
SET OUTBOX=%AGENT_DIR%\outbox
SET REPORTS=%AGENT_DIR%\reports
SET QWEN_API_KEY=sk-6a2bdde5502c4191aef71887d90d7576

IF DEFINED TASK_FILE (
    SET CURRENT_TASK=%TASK_FILE%
    GOTO :RUN_TASK
)

REM ── 检查 inbox 是否有任务
FOR /F "delims=" %%i IN ('dir /b /o-d "%INBOX%\*.json" 2^>nul') DO (
    SET CURRENT_TASK=%INBOX%\%%i & GOTO :RUN_TASK
)
echo inbox 为空，退出 & GOTO :END

:RUN_TASK
FOR %%F IN ("%CURRENT_TASK%") DO SET TASK_ID=%%~nF
SET RESULT_FILE=%OUTBOX%\result_%TASK_ID%.json
SET REPORT_FILE=%REPORTS%\%TASK_ID%.md
SET PROMPT_FILE=%INBOX%\_prompt_%TASK_ID%.txt

echo [INFO] 任务: %TASK_ID%
echo [INFO] 结果: %RESULT_FILE%

REM ── 更新状态 busy
echo {"status":"busy","agent":"%AGENT_ID%","task_id":"%TASK_ID%"} > %AGENT_DIR%\.status

REM ── 生成带系统提示词的提示文件
python -c "
from pathlib import Path
import sys, json
sys.path.insert(0,'D:\\sslb\\my_agent_project')
from prompts import build_task_prompt
t = json.loads(Path(r'%CURRENT_TASK%').read_text('utf-8'))
Path(r'%PROMPT_FILE%').write_text(build_task_prompt('%AGENT_ID%', t), 'utf-8')
print('提示词生成完成')
"

REM ── 调用 Qwen API
echo [INFO] 调用 Qwen 处理任务...
python -c "
import json, os, sys
from pathlib import Path
sys.path.insert(0,'D:\\sslb\\my_agent_project')
from prompts import build_task_prompt

task = json.loads(Path(r'%CURRENT_TASK%').read_text('utf-8'))
prompt = build_task_prompt('%AGENT_ID%', task)

try:
    import dashscope
    dashscope.api_key = '%QWEN_API_KEY%'
    from dashscope import Generation
    resp = Generation.call(
        model='qwen-max',
        messages=[
            {'role':'system','content':prompt},
            {'role':'user','content':json.dumps(task, ensure_ascii=False)}
        ],
        result_format='message'
    )
    content = resp.output.choices[0].message.content
except Exception as e:
    content = f'Qwen API 调用失败: {e}'

result = {
    'task_id': '%TASK_ID%',
    'from': '%AGENT_ID%',
    'status': 'done',
    'summary': content[:1000]
}
Path(r'%RESULT_FILE%').write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')

# 生成报告
md = f'''# %AGENT_ID% 执行报告

**任务**: {result['task_id']}
**状态**: {result['status']}

## 输出摘要
{result.get('summary','')}

## 原始任务
```json
{json.dumps(task, ensure_ascii=False, indent=2)}
```
'''
Path(r'%REPORT_FILE%').write_text(md, 'utf-8')
print('结果文件生成完成')
"

REM ── 归档任务
mkdir %INBOX%\archive 2>nul
MOVE "%CURRENT_TASK%" "%INBOX%\archive\" >nul 2>&1

REM ── 更新状态 idle
echo {"status":"idle","agent":"%AGENT_ID%","last_task":"%TASK_ID%"} > %AGENT_DIR%\.status
echo [%AGENT_ID%] 任务 %TASK_ID% 完成

:END
pause

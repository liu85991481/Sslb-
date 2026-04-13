@echo off
chcp 65001 >nul

SET AGENT_ID=xingbu
SET AGENT_DIR=D:\sslb\%AGENT_ID%
SET INBOX=%AGENT_DIR%\inbox
SET OUTBOX=%AGENT_DIR%\outbox
SET REPORTS=%AGENT_DIR%\reports
SET PROMPT_MODULE=XING_BU_PROMPT

SET ANTHROPIC_BASE_URL=https://api.svips.org
SET ANTHROPIC_AUTH_TOKEN=sk-510defdaa8231977542f69248b2e5477ff49750b7a31e1a5d7a5f63cd1bbda7b
SET ANTHROPIC_MODEL=MiniMax-M2.7
SET CLAUDE_CODE_GIT_BASH_PATH=D:\asdfg\Git\bin\bash.exe

IF DEFINED TASK_FILE (
    SET CURRENT_TASK=%TASK_FILE%
    GOTO :RUN_TASK
)

FOR /F "delims=" %%i IN ('dir /b /o-d "%INBOX%\*.json" 2^>nul') DO (
    SET CURRENT_TASK=%INBOX%\%%i & GOTO :RUN_TASK
)
echo inbox empty, exit & GOTO :END

:RUN_TASK
FOR %%F IN ("%CURRENT_TASK%") DO SET TASK_ID=%%~nF
SET RESULT_FILE=%OUTBOX%\result_%TASK_ID%.json
SET RAW_FILE=%OUTBOX%\%TASK_ID%_raw.txt
SET REPORT_FILE=%REPORTS%\%TASK_ID%.md
SET PROMPT_FILE=%INBOX%\_prompt_%TASK_ID%.txt

echo [INFO] Task: %TASK_ID%
echo [INFO] Result: %RESULT_FILE%

REM Update status busy
echo {"status":"busy","agent":"%AGENT_ID%","task_id":"%TASK_ID%"} > %AGENT_DIR%\.status

REM Generate prompt
python -c "import sys; sys.path.insert(0,'D:/sslb/my_agent_project'); from prompts import %PROMPT_MODULE%; from pathlib import Path; import json; t=json.loads(Path(r'%CURRENT_TASK%').read_text('utf-8')); p=%PROMPT_MODULE%+chr(10)+chr(10)+'## Task'+chr(10)+json.dumps(t,ensure_ascii=False)+chr(10); Path(r'%PROMPT_FILE%').write_text(p,'utf-8')"

REM Call Claude
echo [INFO] Calling Claude...
claude --model %ANTHROPIC_MODEL% --print < "%PROMPT_FILE%" > "%RAW_FILE%" 2>&1

REM Extract JSON result
python D:\sslb\my_agent_project\extract_result.py "%RAW_FILE%" "%RESULT_FILE%" "%TASK_ID%" "%AGENT_ID%"

REM Archive task
mkdir %INBOX%\archive 2>nul
MOVE "%CURRENT_TASK%" "%INBOX%\archive\" >nul 2>&1

REM Update status idle
echo {"status":"idle","agent":"%AGENT_ID%","last_task":"%TASK_ID%"} > %AGENT_DIR%\.status
echo [%AGENT_ID%] Task %TASK_ID% completed

:END
pause

@echo off
chcp 65001 >nul

SET ROOT=D:\sslb
SET TEST_AGENT=zhongshusheng
SET AGENT_DIR=%ROOT%\%TEST_AGENT%
SET INBOX=%AGENT_DIR%\inbox

echo ==========================================
echo   SSLB Agent Test
echo ==========================================

REM Create test task via Python
echo [1/3] Creating test task...
python -c "import json,sys; from pathlib import Path; from datetime import datetime; t={'task_id':'test_%time:~0,2%%time:~3,2%%time:~6,2%','from':'human','to':'%TEST_AGENT%','content':'login system','priority':'high'}; Path('%INBOX%\\'+t['task_id']+'.json').write_text(json.dumps(t,ensure_ascii=False),encoding='utf-8'); print(t['task_id'])"

echo [2/3] Checking inbox...
dir /b "%INBOX%\*.json"

echo [3/3] Ready
echo ==========================================
echo   NEXT: Run start-claude.bat
echo ==========================================
pause

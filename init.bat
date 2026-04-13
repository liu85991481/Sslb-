@echo off
chcp 65001 >nul

set ROOT=D:\sslb

echo.
echo ╔══════════════════════════════════════╗
echo ║     三省六部多智能体系统初始化       ║
echo ╚══════════════════════════════════════╝
echo.

:: 创建消息总线目录
echo [1/4] 创建消息总线目录...
if not exist "%ROOT%\.bus" mkdir "%ROOT%\.bus"
if not exist "%ROOT%\.bus\inbox" mkdir "%ROOT%\.bus\inbox"
if not exist "%ROOT%\.bus\outbox" mkdir "%ROOT%\.bus\outbox"
if not exist "%ROOT%\.bus\logs" mkdir "%ROOT%\.bus\logs"
echo       OK .bus 目录创建完成

:: 创建各智能体 inbox/outbox
echo [2/4] 创建智能体通信目录...
for %%a in (zhongshusheng menxiasheng shangshusheng libu hubu liyibu bingbu xingbu gongbu) do (
    if not exist "%ROOT%\%%a\inbox" mkdir "%ROOT%\%%a\inbox"
    if not exist "%ROOT%\%%a\outbox" mkdir "%ROOT%\%%a\outbox"
)
echo       OK 智能体通信目录创建完成

:: 创建路由配置
echo [3/4] 创建路由配置...
(
    echo {
    echo   "routes": {
    echo     "zhongshusheng": ["menxiasheng", "shangshusheng"],
    echo     "menxiasheng": [],
    echo     "shangshusheng": ["libu", "hubu", "liyibu", "bingbu", "xingbu", "gongbu"],
    echo     "libu": [],
    echo     "hubu": [],
    echo     "liyibu": [],
    echo     "bingbu": [],
    echo     "xingbu": [],
    echo     "gongbu": []
    echo   }
    echo }
) > "%ROOT%\.bus\routes.json"
echo       OK routes.json 创建完成

:: 创建状态文件
echo [4/4] 创建系统状态文件...
(
    echo {
    echo   "system": "三省六部多智能体系统",
    echo   "version": "1.0",
    echo   "initialized": "%date% %time%"
    echo }
) > "%ROOT%\.bus\system.json"
echo       OK system.json 创建完成

echo.
echo ╔══════════════════════════════════════╗
echo ║  OK 初始化完成！下一步：              ║
echo ║                                        ║
echo ║  1. 运行 python main.py 启动调度器    ║
echo ║  2. 运行任意 .bat 测试单个智能体      ║
echo ║                                        ║
echo ║  目录结构:                             ║
echo ║  D:\sslb\.bus\  消息总线              ║
echo ║  D:\sslb\*.bat  各智能体启动脚本     ║
echo ╚══════════════════════════════════════╝
echo.
pause

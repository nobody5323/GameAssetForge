@echo off
chcp 65001 >nul
title GameAsset Forge — 一键启动
echo ============================================
echo   GameAsset Forge — 一键启动
echo ============================================
echo.

:: ── 后端启动 ──
echo [1/2] 启动后端 (uvicorn :8000)...
cd /d "%~dp0backend"
start "GF-Backend" cmd /c "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
echo        ^> PID: %errorlevel%
echo.

:: ── 前端启动 ──
echo [2/2] 启动前端 (vite :4174)...
cd /d "%~dp0frontend"
start "GF-Frontend" cmd /c "npm run dev"
echo        ^> PID: %errorlevel%
echo.

:: ── 打开浏览器 ──
timeout /t 3 /nobreak >nul
start http://127.0.0.1:4174
echo ============================================
echo   前端: http://127.0.0.1:4174
echo   后端: http://127.0.0.1:8000
echo   API文档: http://127.0.0.1:8000/docs
echo ============================================
echo.
echo 关闭两个终端窗口即可停止服务。
echo.
pause

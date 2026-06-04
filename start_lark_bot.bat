@echo off
chcp 65001 >nul 2>&1
title PPT Agent Lark Bot

set "VENV_PYTHON=F:\photo_to_vedio\pythonProject\.venv311\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    echo 找不到 Python：%VENV_PYTHON%
    pause
    exit /b 1
)

echo ============================================================
echo   PPT Agent Lark Bot
echo ============================================================
echo.

cd /d "%~dp0"

"%VENV_PYTHON%" -m ppt_agent.lark_bot

echo.
echo Bot exited with code: %errorlevel%
echo.
pause

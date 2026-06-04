# PPT Agent 飞书机器人 - PowerShell 启动脚本
$ErrorActionPreference = "Continue"

$VenvPython = "F:\photo_to_vedio\pythonProject\.venv311\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "找不到 Python：$VenvPython"
    Read-Host "按 Enter 关闭窗口"
    exit 1
}

Write-Host "============================================================"
Write-Host "  PPT Agent 飞书机器人"
Write-Host "============================================================"
Write-Host ""

Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

& $VenvPython -m ppt_agent.lark_bot

Write-Host ""
Write-Host "机器人已退出。"
Read-Host "按 Enter 关闭窗口"

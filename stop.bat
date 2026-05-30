@echo off
chcp 65001 >nul
:: =======================================
:: 运行项目一键停止脚本 (STOP)
:: 自动清理端口并自动执行 docker-compose down
:: =======================================
echo 正在进入 PowerShell 执行引擎停止服务...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop.ps1"
pause

@echo off
chcp 65001 >nul
:: =======================================
:: 运行项目一键启动脚本 (STAR)
:: 自动清理端口冲突、拉起Docker及前后端
:: =======================================
echo 正在进入 PowerShell 执行引擎...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0star.ps1"
pause

<#
.SYNOPSIS
一键停止脚本 (stop.ps1) - 自动关闭项目相关的所有服务。

.DESCRIPTION
此脚本将执行:
1. 检查并结束指定端口 (5173, 5174, 8000) 上运行的前后端服务进程。
2. 使用 docker-compose down 停止并移除 Docker 容器。
#>

Write-Host "============================" -ForegroundColor Cyan
Write-Host " 运行项目一键停止脚本 (STOP) " -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

$BasePath = $PSScriptRoot
if ([string]::IsNullOrEmpty($BasePath)) {
    $BasePath = (Get-Location).Path
}
Set-Location -Path $BasePath
Write-Host "[*] 工作目录: $BasePath" -ForegroundColor Green

# === 1. 清理端口占用 ===
function Kill-ProcessByPort {
    param([int]$port)
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($conn in $conns) {
            $pidToKill = $conn.OwningProcess
            if ($pidToKill -ne 0 -and $pidToKill -ne 4) {
                $proc = Get-Process -Id $pidToKill -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "[*] 正在结束端口 $port 上的进程 $($proc.ProcessName) (PID: $pidToKill)..." -ForegroundColor Yellow
                    Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
                    Write-Host "[+] 进程已被终止。" -ForegroundColor Green
                }
            }
        }
    } else {
        Write-Host "[-] 端口 $port 当前未被占用。" -ForegroundColor DarkGray
    }
}

Write-Host "[*] 正在关闭前端/后端服务进程..." -ForegroundColor Cyan
Kill-ProcessByPort -port 8000
Kill-ProcessByPort -port 5173
Kill-ProcessByPort -port 5174

# === 2. 停止 Docker 容器 ===
Write-Host "[*] 正在关闭 Docker 容器服务 (docker-compose down)..." -ForegroundColor Cyan
docker-compose down

Write-Host "============================" -ForegroundColor Cyan
Write-Host " [*] 所有项目服务已成功停止 " -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Start-Sleep -Seconds 3


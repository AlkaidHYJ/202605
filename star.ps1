<#
.SYNOPSIS
一键启动脚本 (star.ps1) - 自动启动本项目的环境、后台和前端。

.DESCRIPTION
使用方法:
1. 右键单击此文件，选择「使用 PowerShell 运行」
2. 或者在 PowerShell 命令行中直接输入: .\star.ps1

此脚本将依次执行:
1. 启动本地 Docker Desktop（用于 docker-compose 服务的依赖环境）。
2. 通过 docker-compose 启动数据库、Redis 等依赖服务。
3. 自动检测前端和后端相应的端口 (5173, 5174, 8000)，若被占用则自动终止相关进程，消除冲突。
4. 启动后端 (FastAPI, 端口 8000)。
5. 启动前端应用 (前端用户端: 5173, 前端管理端: 5174)。
6. 等待后端健康检查通过后，自动在系统默认浏览器中打开用户端和管理端的页面。

.NOTES
请确保本地已配置好 Node.js 和 Python 的相关依赖。
#>

Write-Host "============================" -ForegroundColor Cyan
Write-Host " 运行项目一键启动脚本 (STAR) " -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

# === 切换工作目录至脚本所在目录 ===
$BasePath = $PSScriptRoot
if ([string]::IsNullOrEmpty($BasePath)) {
    $BasePath = (Get-Location).Path
}
Set-Location -Path $BasePath
Write-Host "[*] 已切换目录到: $BasePath" -ForegroundColor Green

# === 0. 启动 Docker Desktop ===
Write-Host "[*] 检查 Docker Desktop 运行状态..." -ForegroundColor Yellow
$dockerProcess = Get-Process "*Docker Desktop*" -ErrorAction SilentlyContinue
if (-not $dockerProcess) {
    Write-Host "[-] 本地未运行 Docker Desktop，尝试启动..." -ForegroundColor Yellow
    $DockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $DockerPath) {
        Start-Process -NoNewWindow -FilePath $DockerPath
        Write-Host "[-] 等待 Docker 守护进程启动，这可能需要几十秒..."
        $dockerReady = $false
        for ($i = 0; $i -lt 30; $i++) {
            docker info >$null 2>&1
            if ($LASTEXITCODE -eq 0) {
                $dockerReady = $true
                break
            }
            Start-Sleep -Seconds 2
        }
        if ($dockerReady) {
            Write-Host "[*] Docker守护进程已启动" -ForegroundColor Green
        } else {
            Write-Host "[!] Docker 启动可能较慢或路径不正确，请确保它正在运行" -ForegroundColor Red
        }
    } else {
        Write-Host "[!] 未找到默认路径下的 Docker Desktop，请手动启动。" -ForegroundColor Red
    }
} else {
    Write-Host "[*] Docker Desktop 已在运行中。" -ForegroundColor Green
}

# === 1. 启动 docker-compose 环境 ===
Write-Host "[*] 启动 Docker 容器依赖服务 (docker compose up -d)..." -ForegroundColor Yellow
$composeCmd = Get-Command docker-compose -ErrorAction SilentlyContinue
if ($composeCmd) {
    docker-compose up -d
} else {
    docker compose up -d
}

# === 2. 自动检测端口并处理冲突 ===
function Kill-ProcessByPort {
    param([int]$port)
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($conn in $conns) {
            $pidToKill = $conn.OwningProcess
            if ($pidToKill -ne 0 -and $pidToKill -ne 4) {
                $proc = Get-Process -Id $pidToKill -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "[!] 发现端口 $port 被进程 $($proc.ProcessName) (PID: $pidToKill) 占用, 正在清理..." -ForegroundColor Red
                    Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
                    Write-Host "[*] 占用进程已被终止。" -ForegroundColor Green
                }
            }
        }
        Start-Sleep -Seconds 1
    }
}

Write-Host "[*] 检查并清理应用端口冲突 (5173, 5174, 8000)..." -ForegroundColor Yellow
Kill-ProcessByPort -port 8000
Kill-ProcessByPort -port 5173
Kill-ProcessByPort -port 5174

# === 2.5 等待依赖服务端口就绪 ===
function Wait-Port {
    param([int]$port, [int]$retry = 20)
    for ($i = 0; $i -lt $retry; $i++) {
        $conn = Test-NetConnection -ComputerName 127.0.0.1 -Port $port -WarningAction SilentlyContinue
        if ($conn.TcpTestSucceeded) {
            return $true
        }
        Start-Sleep -Seconds 2
    }
    return $false
}

Write-Host "[*] 等待 MySQL (8306) 与 Redis (6379) 就绪..." -ForegroundColor Yellow
$mysqlReady = Wait-Port -port 8306
$redisReady = Wait-Port -port 6379
if (-not $mysqlReady) {
    Write-Host "[!] MySQL 未就绪，后端可能无法连接数据库。" -ForegroundColor Red
}
if (-not $redisReady) {
    Write-Host "[!] Redis 未就绪，部分功能可能不可用。" -ForegroundColor Red
}

# === 3. 分发并后台启动各个服务 ===

# 启动Backend
Write-Host "[*] 启动后端服务 (8000 端口)..." -ForegroundColor Yellow
$BackendArgs = "-NoExit", "-Command", "Set-Location `"$BasePath\backend`"; `$venvPy = Join-Path (Get-Location) '.venv\Scripts\python.exe'; if (Test-Path `$venvPy) { & `$venvPy -m uvicorn app.main:app --host 0.0.0.0 --port 8000 } else { python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 }"
Start-Process -FilePath "powershell.exe" -ArgumentList $BackendArgs -WindowStyle Minimized

# 启动前端-User
Write-Host "[*] 启动前端应用 - 用户端 (5173 端口)..." -ForegroundColor Yellow
$FrontendUserArgs = "-NoExit", "-Command", "Set-Location `"$BasePath\frontend-user`"; npm.cmd run dev"
Start-Process -FilePath "powershell.exe" -ArgumentList $FrontendUserArgs -WindowStyle Minimized

# 启动前端-Admin
Write-Host "[*] 启动前端应用 - 管理端 (5174 端口)..." -ForegroundColor Yellow
$FrontendAdminArgs = "-NoExit", "-Command", "Set-Location `"$BasePath\frontend-admin`"; npm.cmd run dev"
Start-Process -FilePath "powershell.exe" -ArgumentList $FrontendAdminArgs -WindowStyle Minimized

# === 4. 等待后端就绪 ===
Write-Host "[*] 正在等待后端服务就绪..." -ForegroundColor Yellow
$retryCount = 0
$isBackendOk = $false
while ($retryCount -lt 15) {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -ErrorAction Stop
        if ($response.status -eq "ok") {
            $isBackendOk = $true
            break
        }
    } catch {
        # ignore errors during retry
    }
    Start-Sleep -Seconds 2
    $retryCount++
}

if ($isBackendOk) {
    Write-Host "[*] 后端服务已就绪！" -ForegroundColor Green
} else {
    Write-Host "[!] 后端服务响应超时，启动可能较慢或出现报错，请检查弹出的后端终端。" -ForegroundColor Red
}

# 等待前端组件完成首次编译打包
Write-Host "[*] 等待前端服务初始化..." -ForegroundColor Yellow
Start-Sleep -Seconds 4

# === 5. 自动在浏览器中打开页面 ===
Write-Host "[*] 在默认浏览器中自动打开相关页面..." -ForegroundColor Yellow
Start-Process "http://localhost:5173"
Start-Process "http://localhost:5174"

Write-Host "============================" -ForegroundColor Cyan
Write-Host " [*] 所有服务分发完毕 " -ForegroundColor Cyan
Write-Host " 后端服务测试页: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host " 前端用户端:     http://localhost:5173" -ForegroundColor Cyan
Write-Host " 前端控制台:     http://localhost:5174" -ForegroundColor Cyan
Write-Host " 终端窗口已在后台打开，可查阅运行日志" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Start-Sleep -Seconds 3


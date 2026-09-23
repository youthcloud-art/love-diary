$ErrorActionPreference = "Stop"
$backend = Join-Path $PSScriptRoot "..\apps\backend"
Set-Location $backend
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "后端虚拟环境不存在，请先在 apps/backend 创建 .venv 并安装 requirements.txt"
}
& ".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

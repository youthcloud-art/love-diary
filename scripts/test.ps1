$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$python = Join-Path $root "apps\backend\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "后端虚拟环境不存在" }
Set-Location $root
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

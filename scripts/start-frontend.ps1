$ErrorActionPreference = "Stop"
$frontend = Join-Path $PSScriptRoot "..\apps\frontend"
Set-Location $frontend
if (-not (Test-Path "node_modules")) {
    throw "前端依赖不存在，请先在 apps/frontend 运行 npm install"
}
& npm.cmd run dev:h5 -- --host 127.0.0.1

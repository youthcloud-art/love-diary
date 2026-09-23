$ErrorActionPreference = "Stop"
$frontend = Resolve-Path (Join-Path $PSScriptRoot "..\apps\frontend")
Set-Location $frontend
& npm.cmd run build:h5
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& npm.cmd run build:mp-weixin
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

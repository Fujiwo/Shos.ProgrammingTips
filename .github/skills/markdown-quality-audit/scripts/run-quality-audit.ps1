# check_markdown.py を Windows から実行するためのラッパー。
# 引数はそのまま check_markdown.py に渡す (例: run-quality-audit.cmd docs --forbid-mermaid)。

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

$env:PYTHONUTF8 = "1"
& $python (Join-Path $scriptDir "check_markdown.py") @args
exit $LASTEXITCODE

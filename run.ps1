Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot
python -m app.main


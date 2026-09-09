$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path upstream/flyvis)) {
    git clone https://github.com/TuragaLab/flyvis.git upstream/flyvis
    if ($LASTEXITCODE -ne 0) { throw 'Clone failed' }
    git -C upstream/flyvis checkout 92b3845cc426dd309a1a0e1b3890156c42e14021
    if ($LASTEXITCODE -ne 0) { throw 'Checkout failed' }
}
if (-not (Test-Path .venv-vision/Scripts/python.exe)) {
    .venv/Scripts/python.exe -m venv .venv-vision
    if ($LASTEXITCODE -ne 0) { throw 'Environment creation failed' }
}
.venv-vision/Scripts/python.exe -m pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-vision-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Install failed' }
.venv-vision/Scripts/python.exe scripts/download_flyvis_models.py
if ($LASTEXITCODE -ne 0) { throw 'Model download failed' }

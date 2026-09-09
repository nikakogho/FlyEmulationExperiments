$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force upstream,data | Out-Null
if (!(Test-Path upstream/fly-api/.git)) {
    git clone https://github.com/dtch1997/fly-api.git upstream/fly-api
    if ($LASTEXITCODE) { throw 'fly-api clone failed' }
    git -C upstream/fly-api checkout --detach a6ad07a810b1a43cd0356149c07b32105eb46d2a
    if ($LASTEXITCODE) { throw 'fly-api revision selection failed' }
}
if (!(Test-Path upstream/Drosophila_brain_model/.git)) {
    git clone https://github.com/philshiu/Drosophila_brain_model.git upstream/Drosophila_brain_model
    if ($LASTEXITCODE) { throw 'model clone failed' }
    git -C upstream/Drosophila_brain_model checkout --detach 91bdd1e7dcf193f3e7ca5a8933497fcef63b7960
    if ($LASTEXITCODE) { throw 'model revision selection failed' }
}
# Existing checkouts are verified, never reset over local edits.
$flyCommit = git -C upstream/fly-api rev-parse HEAD
$modelCommit = git -C upstream/Drosophila_brain_model rev-parse HEAD
if ($flyCommit -ne 'a6ad07a810b1a43cd0356149c07b32105eb46d2a') {
    throw 'fly-api revision differs; select the pinned revision in a clean checkout before continuing'
}
if ($modelCommit -ne '91bdd1e7dcf193f3e7ca5a8933497fcef63b7960') {
    throw 'Shiu model revision differs; select the pinned revision in a clean checkout before continuing'
}
if (!(Test-Path data/annotations.tsv)) {
    Invoke-WebRequest 'https://raw.githubusercontent.com/flyconnectome/flywire_annotations/8587524c1748ce5ef2080822a2fc890fc03bf597/supplemental_files/Supplemental_file1_neuron_annotations.tsv' -OutFile data/annotations.tsv
}
if ((Get-FileHash data/annotations.tsv).Hash -ne '9A4F8B2F843196074431EBD7CD883536AFA1BE86C8A4CE90970441E8BE81D1BE') { throw 'Annotation checksum mismatch' }
if (!(Test-Path .venv/Scripts/python.exe)) { uv venv .venv --python 3.12 }
uv pip install --python .venv/Scripts/python.exe -r requirements-lock.txt
if ($LASTEXITCODE) { throw 'Dependency installation failed' }
uv pip check --python .venv/Scripts/python.exe
if ($LASTEXITCODE) { throw 'Dependency check failed' }

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$huangRepo = 'upstream/Luo_Huang_2024_MB_model'
$huangCommit = '5d7c08a9a88f923169a0c3008aca68af421e9a7f'
if (!(Test-Path "$huangRepo/.git")) {
    git clone https://github.com/schnitzer-lab/Luo_Huang_2024_MB_model.git $huangRepo
    if ($LASTEXITCODE) { throw 'Author repository clone failed' }
    git -C $huangRepo checkout --detach $huangCommit
    if ($LASTEXITCODE) { throw 'Could not select pinned author revision' }
}
if ((git -C $huangRepo rev-parse HEAD) -ne $huangCommit) {
    throw 'Existing author checkout differs; no local files were reset'
}
New-Item -ItemType Directory -Force research/huang2024 | Out-Null
$huangFiles = @(
    @{Name='supplement.pdf'; Number='3'; Extension='pdf'},
    @{Name='figure5.xlsx'; Number='10'; Extension='xlsx'},
    @{Name='extended10.xlsx'; Number='20'; Extension='xlsx'}
)
foreach ($huangFile in $huangFiles) {
    $huangTarget = Join-Path 'research/huang2024' $huangFile.Name
    if (!(Test-Path $huangTarget)) {
        $huangUrl = 'https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-07819-w/MediaObjects/41586_2024_7819_MOESM' + $huangFile.Number + '_ESM.' + $huangFile.Extension
        Invoke-WebRequest $huangUrl -OutFile $huangTarget
    }
}
if (!(Test-Path '.venv/Scripts/python.exe')) {
    throw 'Run setup.ps1 first to install the project Python environment'
}
.venv/Scripts/python.exe scripts/record_huang_provenance.py
if ($LASTEXITCODE) { throw 'Research provenance validation failed' }
Write-Output 'Research sources verified. Run .venv/Scripts/python.exe scripts/check_huang2024.py; the published-figure gate currently fails and returns exit 1.'

<#
.SYNOPSIS
    Clone or update the PSXRecomp engine checkout that the code documentation
    is generated from, at the commit pinned in engine-pin.json.

.DESCRIPTION
    The engine (Alexbeav/psxrecomp) is not part of this repository. It is
    fetched into code-docs/.engine (git-ignored) so Doxygen can index it and the
    guide can embed its source. Re-run this after changing engine-pin.json.

.PARAMETER Force
    Discard any local changes in .engine and re-checkout the pinned commit.
#>
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$docsRoot = Split-Path -Parent $PSScriptRoot
$pin = Get-Content -Raw -LiteralPath (Join-Path $docsRoot "engine-pin.json") | ConvertFrom-Json
$engine = Join-Path $docsRoot ".engine"

if (-not (Test-Path -LiteralPath (Join-Path $engine ".git"))) {
    Write-Host "Cloning $($pin.repository) into $engine" -ForegroundColor Cyan
    git clone --quiet $pin.repository $engine
    if ($LASTEXITCODE -ne 0) { throw "git clone failed" }
}

Push-Location $engine
try {
    $have = git cat-file -t $pin.commit 2>$null
    if ($have -ne "commit") {
        Write-Host "Fetching $($pin.commit)" -ForegroundColor Cyan
        git fetch --quiet origin
        if ($LASTEXITCODE -ne 0) { throw "git fetch failed" }
    }
    if ($Force) { git reset --quiet --hard }
    git checkout --quiet --detach $pin.commit
    if ($LASTEXITCODE -ne 0) { throw "git checkout $($pin.commit) failed" }
    Write-Host "Engine at $(git rev-parse --short HEAD) ($($pin.commit_date))" -ForegroundColor Green
} finally {
    Pop-Location
}

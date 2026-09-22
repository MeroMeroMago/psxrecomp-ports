<#
.SYNOPSIS
    Build the complete code-documentation site: the MkDocs guide plus the
    Doxygen API reference, into code-docs/site.

.DESCRIPTION
    Steps:
      1. Ensure the engine checkout exists (scripts/fetch-engine.ps1).
      2. mkdocs build  -> code-docs/site            (the narrative guide)
      3. doxygen       -> code-docs/site/api        (source browser + graphs)
    Requirements: Python 3 with mkdocs-material, Doxygen 1.9.1+, Graphviz (dot).

.PARAMETER SkipDoxygen
    Only rebuild the guide (fast; useful while editing pages).

.PARAMETER SkipMkDocs
    Only rebuild the API reference.

.PARAMETER Open
    Open site/index.html in the default browser when done.
#>
param(
    [switch]$SkipDoxygen,
    [switch]$SkipMkDocs,
    [switch]$Open
)

$ErrorActionPreference = "Stop"
$docsRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $docsRoot
$site = Join-Path $docsRoot "site"

function Find-Tool([string]$Name, [string[]]$Candidates) {
    $cmd = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cmd) { return $cmd.Source }
    foreach ($c in $Candidates) { if (Test-Path -LiteralPath $c) { return $c } }
    throw "$Name not found. Install it and make sure it is on PATH."
}

& (Join-Path $PSScriptRoot "fetch-engine.ps1")

if (-not $SkipMkDocs) {
    Write-Host "== mkdocs build ==" -ForegroundColor Cyan
    Push-Location $repoRoot
    try {
        python -m mkdocs build --strict -f (Join-Path $docsRoot "mkdocs.yml")
        if ($LASTEXITCODE -ne 0) { throw "mkdocs build failed" }
    } finally { Pop-Location }
}

if (-not $SkipDoxygen) {
    $doxygen = Find-Tool "doxygen" @("C:\Program Files\doxygen\bin\doxygen.exe")
    $dot = Find-Tool "dot" @("C:\Program Files\Graphviz\bin\dot.exe")
    $env:PSX_DOCS_DOT_PATH = Split-Path -Parent $dot
    Write-Host "== doxygen ($doxygen, dot in $env:PSX_DOCS_DOT_PATH) ==" -ForegroundColor Cyan
    Push-Location $docsRoot
    try {
        New-Item -ItemType Directory -Force $site | Out-Null
        & $doxygen Doxyfile
        if ($LASTEXITCODE -ne 0) { throw "doxygen failed" }
    } finally { Pop-Location }
    $warnings = Join-Path $docsRoot "doxygen-warnings.log"
    if (Test-Path -LiteralPath $warnings) {
        $count = (Get-Content -LiteralPath $warnings | Measure-Object -Line).Lines
        Write-Host "Doxygen finished with $count warning lines (see doxygen-warnings.log)."
    }
}

if (-not $SkipDoxygen -and -not $SkipMkDocs) {
    Write-Host "== link check ==" -ForegroundColor Cyan
    python (Join-Path $PSScriptRoot "check-links.py") $site
    if ($LASTEXITCODE -ne 0) { throw "broken links in the built site (see above)" }
}

Write-Host "Site built: $(Join-Path $site 'index.html')" -ForegroundColor Green
if ($Open) { Start-Process (Join-Path $site "index.html") }

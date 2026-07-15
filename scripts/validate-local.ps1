$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$env:UV_CACHE_DIR = Join-Path $RepoRoot ".uv-cache"
$LocalTempRoot = Join-Path $RepoRoot ".tmp"
$env:TEMP = $LocalTempRoot
$env:TMP = $LocalTempRoot
$env:TMPDIR = $LocalTempRoot
$env:PIP_CACHE_DIR = Join-Path $LocalTempRoot "pip-cache"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Name,
        [Parameter(Mandatory = $true)]
        [scriptblock] $Command
    )

    Write-Host ""
    Write-Host "==> $Name"
    & $Command
}

function Stop-StaleWheelSmokeProcesses {
    $processes = Get-Process -Name python, pip -ErrorAction SilentlyContinue
    foreach ($process in $processes) {
        $processPath = $null
        try {
            $processPath = $process.Path
        } catch {
            continue
        }

        if ($processPath -and $processPath -like "*guerilla-wheel-smoke-*") {
            Write-Host "Stopping stale wheel-smoke process $($process.Id): $processPath"
            Stop-Process -Id $process.Id -Force
        }
    }
}

function Invoke-WheelSmoke {
    $distPath = Join-Path $RepoRoot "dist"
    $wheel = Get-ChildItem -Path $distPath -Filter "*.whl" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $wheel) {
        throw "No wheel found in $distPath"
    }

    $wheelVenvName = "guerilla-wheel-smoke-" + [System.Guid]::NewGuid().ToString("N")
    $wheelVenv = Join-Path $LocalTempRoot $wheelVenvName
    python -m venv $wheelVenv

    $venvPython = Join-Path $wheelVenv "Scripts\python.exe"
    $venvGuerilla = Join-Path $wheelVenv "Scripts\guerilla.exe"
    & $venvPython -m pip install --no-deps $wheel.FullName

    $smokeWorkDir = Join-Path $LocalTempRoot "wheel-smoke-workdir"
    New-Item -ItemType Directory -Force -Path $smokeWorkDir | Out-Null
    Push-Location $smokeWorkDir
    try {
        & $venvPython -c "import guerilla; print(guerilla.__version__)"
        & $venvGuerilla --version
        & $venvGuerilla --help
        & $venvGuerilla version --json

        $unexpectedWorkspace = Join-Path $smokeWorkDir ".guerilla"
        if (Test-Path $unexpectedWorkspace) {
            throw "Wheel smoke created unexpected workspace state: $unexpectedWorkspace"
        }
    } finally {
        Pop-Location
    }

    Write-Host "WHEEL_SMOKE_ROOT=$wheelVenv"
}

New-Item -ItemType Directory -Force -Path $env:UV_CACHE_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $LocalTempRoot | Out-Null
New-Item -ItemType Directory -Force -Path $env:PIP_CACHE_DIR | Out-Null
Write-Host "Using UV_CACHE_DIR=$env:UV_CACHE_DIR"
Write-Host "Using local temp root=$LocalTempRoot"
Write-Host "Using PIP_CACHE_DIR=$env:PIP_CACHE_DIR"

Stop-StaleWheelSmokeProcesses

Push-Location $RepoRoot
try {
    Invoke-Step "Verify lockfile" { uv lock --check }
    Invoke-Step "Install dependencies" { uv sync --frozen --extra dev }
    Invoke-Step "Formatting check" { uv run --frozen --extra dev ruff format --check . }
    Invoke-Step "Lint check" { uv run --frozen --extra dev ruff check . }
    Invoke-Step "Static analysis" { uv run --frozen --extra dev mypy src tests }
    Invoke-Step "Tests" { uv run --frozen --extra dev pytest }
    Invoke-Step "Build package" { uv build }
    Invoke-Step "Isolated wheel smoke" { Invoke-WheelSmoke }
} finally {
    Pop-Location
}

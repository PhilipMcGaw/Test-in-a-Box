[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)


$PythonExe = Join-Path $ProjectRoot "python\python.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Portable Python is missing: $PythonExe"
}

if (-not (Test-Path -LiteralPath $Requirements)) {
    throw "requirements.txt is missing: $Requirements"
}

Write-Host "Checking pip..."
& $PythonExe -m pip --version *> $null

if ($LASTEXITCODE -ne 0) {
    Write-Host "pip is missing. Running ensurepip..."
    & $PythonExe -m ensurepip --upgrade
    if ($LASTEXITCODE -ne 0) {
        throw "pip could not be installed."
    }
}

Write-Host "Installing or updating dependencies from requirements.txt..."
& $PythonExe -m pip install `
    --disable-pip-version-check `
    --no-warn-script-location `
    -r $Requirements

if ($LASTEXITCODE -ne 0) {
    throw @"
Dependency installation failed.

The network may be blocking:
  pypi.org
  files.pythonhosted.org

Ask IT to allow those services, or prepare the python folder and packages on
another PC and transfer them to this project.
"@
}

Write-Host "Checking installed dependency consistency..."
& $PythonExe -m pip check
if ($LASTEXITCODE -ne 0) {
    throw "pip reported inconsistent installed dependencies."
}

Write-Host "[PASS] Python dependencies are ready."

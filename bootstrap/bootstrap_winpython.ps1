[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)


function Fail([string] $Message) {
    throw $Message
}

$PythonTarget = Join-Path $ProjectRoot "python"
$PythonExe = Join-Path $PythonTarget "python.exe"

if (Test-Path -LiteralPath $PythonExe) {
    Write-Host "[PASS] Portable Python already exists."
    Write-Host "       $PythonExe"
    exit 0
}

if (Test-Path -LiteralPath $PythonTarget) {
    $Items = @(Get-ChildItem -LiteralPath $PythonTarget -Force)
    if ($Items.Count -gt 0) {
        Fail "The python folder exists but does not contain python.exe. Rename or remove the incomplete folder, then run bootstrap again."
    }
}

$TempRoot = Join-Path $ProjectRoot "_bootstrap_winpython"
$DownloadPath = Join-Path $TempRoot "winpython-download"
$ExtractPath = Join-Path $TempRoot "extracted"

if (Test-Path -LiteralPath $TempRoot) {
    Remove-Item -LiteralPath $TempRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $TempRoot | Out-Null
New-Item -ItemType Directory -Path $ExtractPath | Out-Null

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

Write-Host "Reading the official WinPython checksum manifest..."

$ManifestUri = "https://winpython.github.io/md5_sha1.txt"
$ManifestPath = Join-Path $TempRoot "winpython-checksums.txt"

Invoke-WebRequest `
    -Uri $ManifestUri `
    -UseBasicParsing `
    -OutFile $ManifestPath

if (-not (Test-Path -LiteralPath $ManifestPath)) {
    Fail "The WinPython checksum manifest could not be downloaded."
}

$ManifestLines = Get-Content -LiteralPath $ManifestPath

$PreferredSeries = @("3.13", "3.12")
$SelectedName = $null
$ExpectedSha256 = $null

foreach ($Series in $PreferredSeries) {
    # The official manifest is ordered newest first. Match only stable
    # 64-bit Dot ZIP/EXE filenames with numeric release components.
    $Pattern = (
        "^\s*[0-9a-fA-F]{32}\s*\|\s*" +
        "[0-9a-fA-F]{40}\s*\|\s*" +
        "([0-9a-fA-F]{64})\s*\|\s*" +
        "(Win[Pp]ython64-" +
        [regex]::Escape($Series) +
        "\.[0-9.]+dot\.(?:zip|exe))\s*\|"
    )

    foreach ($Line in $ManifestLines) {
        if ($Line -match $Pattern) {
            $ExpectedSha256 = $Matches[1].ToUpperInvariant()
            $SelectedName = $Matches[2]
            break
        }
    }

    if ($null -ne $SelectedName) {
        break
    }
}

if ($null -eq $SelectedName) {
    Fail "No stable 64-bit WinPython 3.13 or 3.12 Dot ZIP/EXE was found in the official checksum manifest."
}

$Extension = [System.IO.Path]::GetExtension($SelectedName)
$DownloadPath = $DownloadPath + $Extension

# GitHub's normal release-download endpoint does not use the REST API and
# therefore avoids unauthenticated API rate limits.
$DownloadUri = (
    "https://github.com/winpython/winpython/releases/latest/download/" +
    $SelectedName
)

Write-Host "Asset:  $SelectedName"
Write-Host "Source: $DownloadUri"
Write-Host "Downloading the official WinPython release asset..."

try {
    Invoke-WebRequest `
        -Uri $DownloadUri `
        -UseBasicParsing `
        -OutFile $DownloadPath
}
catch {
    Fail @"
The WinPython release asset could not be downloaded.

Asset:
  $SelectedName

Source:
  $DownloadUri

This method does not use the GitHub REST API. If it still fails, the network
may be blocking github.com or objects.githubusercontent.com.

Original error:
  $($_.Exception.Message)
"@
}

if (-not (Test-Path -LiteralPath $DownloadPath)) {
    Fail "The WinPython download did not complete."
}

$Length = (Get-Item -LiteralPath $DownloadPath).Length
if ($Length -lt 1000000) {
    Fail "The downloaded WinPython asset is unexpectedly small ($Length bytes)."
}

Write-Host "Verifying SHA-256 from the official WinPython manifest..."
$ActualSha256 = (
    Get-FileHash -LiteralPath $DownloadPath -Algorithm SHA256
).Hash

if ($ActualSha256 -ne $ExpectedSha256) {
    Fail @"
WinPython SHA-256 verification failed.

Expected:
  $ExpectedSha256

Received:
  $ActualSha256
"@
}

Write-Host "[PASS] SHA-256 verified."

Write-Host "Extracting WinPython..."

if ($Extension -ieq ".zip") {
    Expand-Archive -LiteralPath $DownloadPath -DestinationPath $ExtractPath -Force
}
elseif ($Extension -ieq ".exe") {
    # WinPython Dot downloads are self-extracting 7-Zip archives, not MSI
    # installers. The switches below extract silently without administrator
    # rights.
    $Process = Start-Process `
        -FilePath $DownloadPath `
        -ArgumentList @("-y", "-o$ExtractPath") `
        -Wait `
        -PassThru

    if ($Process.ExitCode -ne 0) {
        Fail "The WinPython self-extracting archive returned exit code $($Process.ExitCode)."
    }
}
else {
    Fail "Unsupported WinPython asset type: $Extension"
}

Write-Host "Locating the portable Python runtime..."

$PythonExecutables = @(
    Get-ChildItem -LiteralPath $ExtractPath -Filter "python.exe" -File -Recurse
)

if ($PythonExecutables.Count -eq 0) {
    Fail "No python.exe files were found after extracting WinPython."
}

$RuntimeCandidates = @()

foreach ($PythonExecutable in $PythonExecutables) {
    $CandidateRoot = $PythonExecutable.Directory.FullName

    $HasLib = Test-Path -LiteralPath (Join-Path $CandidateRoot "Lib")
    $HasDlls = Test-Path -LiteralPath (Join-Path $CandidateRoot "DLLs")
    $HasStdlib = Test-Path -LiteralPath (
        Join-Path $CandidateRoot "Lib\os.py"
    )

    if ($HasLib -and $HasDlls -and $HasStdlib) {
        $RuntimeCandidates += $PythonExecutable.Directory
    }
}

# Remove duplicate directory objects if more than one python.exe search result
# points at the same runtime folder.
$RuntimeCandidates = @(
    $RuntimeCandidates |
    Sort-Object -Property FullName -Unique
)

if ($RuntimeCandidates.Count -ne 1) {
    Write-Host ""
    Write-Host "Extracted python.exe files:"
    foreach ($PythonExecutable in $PythonExecutables) {
        Write-Host "  $($PythonExecutable.FullName)"
    }

    Write-Host ""
    Write-Host "Runtime candidates containing python.exe, Lib, DLLs and Lib\os.py:"
    if ($RuntimeCandidates.Count -eq 0) {
        Write-Host "  (none)"
    }
    else {
        foreach ($Candidate in $RuntimeCandidates) {
            Write-Host "  $($Candidate.FullName)"
        }
    }

    Fail "Expected exactly one usable portable Python runtime after extraction, but found $($RuntimeCandidates.Count)."
}

$RuntimeSource = $RuntimeCandidates[0].FullName
Write-Host "Using portable runtime:"
Write-Host "  $RuntimeSource"

if (Test-Path -LiteralPath $PythonTarget) {
    Remove-Item -LiteralPath $PythonTarget -Recurse -Force
}

Move-Item -LiteralPath $RuntimeSource -Destination $PythonTarget

if (-not (Test-Path -LiteralPath $PythonExe)) {
    Fail "python.exe was not present after extraction."
}

& $PythonExe -c "import sys; print(sys.executable); print(sys.version)"
if ($LASTEXITCODE -ne 0) {
    Fail "The extracted portable Python runtime could not start."
}

Remove-Item -LiteralPath $TempRoot -Recurse -Force
Write-Host "[PASS] Portable Python is ready."
Write-Host "       $PythonExe"

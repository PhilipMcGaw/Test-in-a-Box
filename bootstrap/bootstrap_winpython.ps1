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

$Headers = @{
    "Accept" = "application/vnd.github+json"
    "User-Agent" = "Test-in-a-Box-bootstrap"
}

Write-Host "Finding a stable official WinPython Dot release..."

$Releases = Invoke-RestMethod `
    -Uri "https://api.github.com/repos/winpython/winpython/releases?per_page=30" `
    -Headers $Headers

$PreferredSeries = @("3.13", "3.12")
$SelectedAsset = $null
$SelectedRelease = $null

foreach ($Series in $PreferredSeries) {
    foreach ($Release in $Releases) {
        if ($Release.draft -or $Release.prerelease) {
            continue
        }

        $Candidates = @(
            $Release.assets | Where-Object {
                $_.name -match ("^WinPython64-" + [regex]::Escape($Series) + "\.[0-9.]+dot\.(exe|zip)$")
            }
        )

        if ($Candidates.Count -gt 0) {
            $SelectedAsset = $Candidates |
                Sort-Object @{Expression = { if ($_.name.EndsWith(".zip")) { 0 } else { 1 } }} |
                Select-Object -First 1
            $SelectedRelease = $Release
            break
        }
    }

    if ($null -ne $SelectedAsset) {
        break
    }
}

if ($null -eq $SelectedAsset) {
    Fail "No stable 64-bit WinPython 3.13 or 3.12 Dot release asset was found in the latest official releases."
}

$Extension = [System.IO.Path]::GetExtension($SelectedAsset.name)
$DownloadPath = $DownloadPath + $Extension

Write-Host "Release: $($SelectedRelease.name)"
Write-Host "Asset:   $($SelectedAsset.name)"
Write-Host "Downloading from the official WinPython GitHub release..."

Invoke-WebRequest `
    -Uri $SelectedAsset.browser_download_url `
    -Headers $Headers `
    -OutFile $DownloadPath

if (-not (Test-Path -LiteralPath $DownloadPath)) {
    Fail "The WinPython download did not complete."
}

$Length = (Get-Item -LiteralPath $DownloadPath).Length
if ($Length -lt 1000000) {
    Fail "The downloaded WinPython asset is unexpectedly small ($Length bytes)."
}

if ($SelectedAsset.PSObject.Properties.Name -contains "digest" -and $SelectedAsset.digest) {
    if ($SelectedAsset.digest -match "^sha256:([0-9a-fA-F]{64})$") {
        Write-Host "Verifying published SHA-256 digest..."
        $Expected = $Matches[1].ToUpperInvariant()
        $Actual = (Get-FileHash -LiteralPath $DownloadPath -Algorithm SHA256).Hash
        if ($Actual -ne $Expected) {
            Fail "WinPython SHA-256 verification failed."
        }
        Write-Host "[PASS] SHA-256 verified."
    }
}

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

$RuntimeCandidates = @(
    Get-ChildItem -LiteralPath $ExtractPath -Directory -Recurse |
    Where-Object {
        $_.Name -match "^python-[0-9.]+\.amd64$" -and
        (Test-Path -LiteralPath (Join-Path $_.FullName "python.exe"))
    }
)

if ($RuntimeCandidates.Count -ne 1) {
    Fail "Expected exactly one python-*.amd64 runtime after extraction, but found $($RuntimeCandidates.Count)."
}

if (Test-Path -LiteralPath $PythonTarget) {
    Remove-Item -LiteralPath $PythonTarget -Recurse -Force
}

Move-Item -LiteralPath $RuntimeCandidates[0].FullName -Destination $PythonTarget

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

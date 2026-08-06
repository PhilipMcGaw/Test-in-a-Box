[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)

function Write-Info {
    param([string] $Message)
    Write-Host "[INFO] $Message"
}

function Test-PicoRuntime {
    param([string] $PythonExe)

    if (-not (Test-Path -LiteralPath $PythonExe)) {
        return $false
    }

    # Missing Pico native libraries are an expected optional result.
    # Windows PowerShell 5.1 otherwise converts Python stderr into a
    # terminating NativeCommandError while ErrorActionPreference is Stop.
    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    Push-Location $ProjectRoot
    try {
        & $PythonExe `
            -c "from picosdk.usbtc08 import usbtc08; from picosdk.picohrdl import picohrdl" `
            1>$null `
            2>$null

        $ProbeExitCode = $LASTEXITCODE
        return ($ProbeExitCode -eq 0)
    }
    finally {
        Pop-Location
        $ErrorActionPreference = $PreviousErrorActionPreference
    }
}

function Resolve-PicoInstallerUri {
    param([string] $MetadataUri)

    $Page = Invoke-WebRequest -Uri $MetadataUri -UseBasicParsing
    $DownloadUri = $null

    if ($Page.Links) {
        $Link = $Page.Links |
            Where-Object {
                $_.href -match "PicoSDK_x64(?:_[0-9.]+)?\.exe(?:\?.*)?$"
            } |
            Select-Object -First 1

        if ($null -ne $Link) {
            $DownloadUri = [Uri]::new(
                [Uri] $MetadataUri,
                [string] $Link.href
            ).AbsoluteUri
        }
    }

    if (-not $DownloadUri) {
        $Pattern = 'href=["'']([^"'']*PicoSDK_x64(?:_[0-9.]+)?\.exe(?:\?[^"'']*)?)["'']'
        $Match = [regex]::Match(
            [string] $Page.Content,
            $Pattern,
            [Text.RegularExpressions.RegexOptions]::IgnoreCase
        )

        if ($Match.Success) {
            $DownloadUri = [Uri]::new(
                [Uri] $MetadataUri,
                $Match.Groups[1].Value
            ).AbsoluteUri
        }
    }

    return $DownloadUri
}

$PythonExe = Join-Path $ProjectRoot "python\python.exe"
$VendorRoot = Join-Path $ProjectRoot "vendor\pico"
$InstallerRoot = Join-Path $VendorRoot "installer"
$ManifestPath = Join-Path $VendorRoot "installer-manifest.json"
$MetadataUri = "https://www.picotech.com/downloads/_lightbox/pico-software-development-kit-64bit"

New-Item -ItemType Directory -Path $InstallerRoot -Force | Out-Null

if (Test-PicoRuntime -PythonExe $PythonExe) {
    Write-Host "[PASS] Pico TC-08 and ADC-20/24 runtime support is installed."
    Write-Host "       The official picosdk wrappers and native DLLs loaded."
    exit 0
}

$ExistingInstaller = @(
    Get-ChildItem `
        -LiteralPath $InstallerRoot `
        -Filter "PicoSDK_x64*.exe" `
        -File `
        -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTimeUtc -Descending
) | Select-Object -First 1

if ($null -ne $ExistingInstaller) {
    Write-Info "Pico runtime is not currently available to Test in a Box."
    Write-Info "The official PicoSDK installer is already downloaded:"
    Write-Host "       $($ExistingInstaller.FullName)"
    Write-Host ""
    Write-Info "Bootstrap will not run or delete this installer."
    Write-Info "Administrator rights are required once to install the"
    Write-Info "official Windows Pico drivers and runtime."
    Write-Info "After installation, run bootstrap.bat again."
    exit 0
}

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    Write-Host "Finding the current official 64-bit PicoSDK installer..."
    $DownloadUri = Resolve-PicoInstallerUri -MetadataUri $MetadataUri

    if (-not $DownloadUri) {
        throw "The PicoSDK download link could not be found on the official page."
    }

    $DownloadName = [System.IO.Path]::GetFileName(
        ([Uri] $DownloadUri).AbsolutePath
    )

    if ([string]::IsNullOrWhiteSpace($DownloadName) -or
        -not $DownloadName.EndsWith(".exe")) {
        $DownloadName = "PicoSDK_x64.exe"
    }

    $InstallerPath = Join-Path $InstallerRoot $DownloadName

    Write-Host "Downloading official PicoSDK installer:"
    Write-Host "  $DownloadUri"
    Write-Host "Saving permanently to:"
    Write-Host "  $InstallerPath"

    Invoke-WebRequest `
        -Uri $DownloadUri `
        -UseBasicParsing `
        -OutFile $InstallerPath

    if (-not (Test-Path -LiteralPath $InstallerPath)) {
        throw "The PicoSDK installer was not downloaded."
    }

    $InstallerSize = (Get-Item -LiteralPath $InstallerPath).Length
    if ($InstallerSize -lt 1000000) {
        throw "The downloaded PicoSDK installer is unexpectedly small ($InstallerSize bytes)."
    }

    $InstallerHash = (
        Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256
    ).Hash

    $Manifest = [ordered]@{
        source_page = $MetadataUri
        installer_url = $DownloadUri
        installer_filename = $DownloadName
        installer_sha256 = $InstallerHash
        installer_size_bytes = $InstallerSize
        downloaded_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        installation_required = $true
        administrator_required = $true
        executed_by_bootstrap = $false
        deleted_by_bootstrap = $false
    }

    $Manifest |
        ConvertTo-Json -Depth 4 |
        Set-Content `
            -LiteralPath $ManifestPath `
            -Encoding UTF8

    Write-Host ""
    Write-Host "[PASS] Official PicoSDK installer downloaded."
    Write-Host "       $InstallerPath"
    Write-Host ""
    Write-Info "Bootstrap did not execute the installer."
    Write-Info "Bootstrap will not delete the installer."
    Write-Info "Administrator rights are required once to install the"
    Write-Info "official Windows Pico drivers and runtime."
    Write-Info "After installation, run bootstrap.bat again."
    exit 0
}
catch {
    Write-Host ""
    Write-Info "Pico runtime support remains unavailable."
    Write-Info $_.Exception.Message
    Write-Info "This optional step did not stop the main bootstrap."
    Write-Info "Official download page:"
    Write-Host "       $MetadataUri"
    exit 0
}

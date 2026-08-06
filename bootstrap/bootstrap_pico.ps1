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

    # A missing Pico native runtime is an expected probe result. In Windows
    # PowerShell 5.1, stderr from a native process is surfaced as a
    # NativeCommandError when ErrorActionPreference is Stop. Temporarily use
    # Continue so Python can fail normally and let its exit code decide the
    # result without aborting the whole bootstrap.
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

$PythonExe = Join-Path $ProjectRoot "python\python.exe"
$VendorRoot = Join-Path $ProjectRoot "vendor\pico"
$InstallerRoot = Join-Path $VendorRoot "installer"
$WorkRoot = Join-Path $ProjectRoot "_bootstrap_pico"
$LayoutRoot = Join-Path $WorkRoot "layout"
$BootstrapperPath = Join-Path $LayoutRoot "PicoSDK_x64.exe"
$MetadataUri = "https://www.picotech.com/downloads/_lightbox/pico-software-development-kit-64bit"

New-Item -ItemType Directory -Path $VendorRoot -Force | Out-Null
New-Item -ItemType Directory -Path $InstallerRoot -Force | Out-Null

if (Test-PicoRuntime -PythonExe $PythonExe) {
    Write-Host "[PASS] Pico TC-08 and ADC-20/24 runtime support is installed."
    Write-Host "       The official picosdk wrappers and native DLLs loaded."
    exit 0
}

$ExistingInstaller = @(
    Get-ChildItem -LiteralPath $InstallerRoot -Filter "PicoSDK_x64_*.exe" -File -ErrorAction SilentlyContinue |
    Sort-Object Length -Descending
) | Select-Object -First 1

if ($null -ne $ExistingInstaller) {
    Write-Info "Pico runtime is not currently available to Test in a Box."
    Write-Info "The full offline PicoSDK installer is already downloaded:"
    Write-Host "       $($ExistingInstaller.FullName)"
    Write-Host ""
    Write-Info "Administrator rights are required once to install the"
    Write-Info "official Windows Pico drivers and runtime."
    Write-Info "After installation, run bootstrap.bat again."
    exit 0
}

try {
    if (Test-Path -LiteralPath $WorkRoot) {
        Remove-Item -LiteralPath $WorkRoot -Recurse -Force
    }

    New-Item -ItemType Directory -Path $LayoutRoot -Force | Out-Null
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    Write-Host "Finding the current official PicoSDK web bootstrapper..."
    $Page = Invoke-WebRequest -Uri $MetadataUri -UseBasicParsing
    $DownloadUri = $null

    if ($Page.Links) {
        $Link = $Page.Links |
            Where-Object {
                $_.href -match "PicoSDK_x64(?:_[0-9.]+)?\.exe(?:\?.*)?$"
            } |
            Select-Object -First 1

        if ($null -ne $Link) {
            $DownloadUri = [Uri]::new([Uri] $MetadataUri, [string] $Link.href).AbsoluteUri
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
            $DownloadUri = [Uri]::new([Uri] $MetadataUri, $Match.Groups[1].Value).AbsoluteUri
        }
    }

    if (-not $DownloadUri) {
        throw "The PicoSDK download link could not be found on the official page."
    }

    Write-Host "Downloading PicoSDK web bootstrapper:"
    Write-Host "  $DownloadUri"

    Invoke-WebRequest -Uri $DownloadUri -UseBasicParsing -OutFile $BootstrapperPath

    if (-not (Test-Path -LiteralPath $BootstrapperPath)) {
        throw "The PicoSDK web bootstrapper was not downloaded."
    }

    $BootstrapperHash = (Get-FileHash -LiteralPath $BootstrapperPath -Algorithm SHA256).Hash

    Write-Host "Bootstrapper SHA-256:"
    Write-Host "  $BootstrapperHash"
    Write-Host ""
    Write-Host "Requesting the complete offline PicoSDK bundle..."
    Write-Host "This downloads files only and does not install the SDK."

    $Process = Start-Process `
        -FilePath $BootstrapperPath `
        -ArgumentList @("/layout") `
        -WorkingDirectory $LayoutRoot `
        -Wait `
        -PassThru

    if ($Process.ExitCode -ne 0) {
        throw "PicoSDK /layout returned exit code $($Process.ExitCode)."
    }

    $FullInstaller = @(
        Get-ChildItem -LiteralPath $LayoutRoot -Filter "PicoSDK_x64_*.exe" -File -ErrorAction SilentlyContinue |
        Where-Object {
            $_.FullName -ne $BootstrapperPath -and
            $_.Length -gt 10000000
        } |
        Sort-Object Length -Descending
    ) | Select-Object -First 1

    if ($null -eq $FullInstaller) {
        Write-Host ""
        Write-Host "Files created by /layout:"
        Get-ChildItem -LiteralPath $LayoutRoot -File |
            ForEach-Object {
                Write-Host ("  {0} ({1} bytes)" -f $_.Name, $_.Length)
            }
        throw "The complete offline PicoSDK installer was not found after /layout."
    }

    $Destination = Join-Path $InstallerRoot $FullInstaller.Name
    Copy-Item -LiteralPath $FullInstaller.FullName -Destination $Destination -Force

    $InstallerHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash

    $Manifest = [ordered]@{
        source_page = $MetadataUri
        bootstrapper_url = $DownloadUri
        bootstrapper_sha256 = $BootstrapperHash
        offline_installer = $FullInstaller.Name
        offline_installer_sha256 = $InstallerHash
        downloaded_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        installation_required = $true
        administrator_required = $true
    }

    $Manifest |
        ConvertTo-Json -Depth 4 |
        Set-Content -LiteralPath (Join-Path $VendorRoot "installer-manifest.json") -Encoding UTF8

    Remove-Item -LiteralPath $WorkRoot -Recurse -Force

    Write-Host ""
    Write-Host "[PASS] Full offline PicoSDK installer downloaded."
    Write-Host "       $Destination"
    Write-Host ""
    Write-Info "Bootstrap did not execute the installer."
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

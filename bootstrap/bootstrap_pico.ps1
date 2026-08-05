[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)

function Fail {
    param([string] $Message)
    throw $Message
}

$VendorRoot = Join-Path $ProjectRoot "vendor\pico"
$RuntimeRoot = Join-Path $VendorRoot "runtime"
$Tc08Dll = Join-Path $RuntimeRoot "usb_tc08.dll"
$HrdlDll = Join-Path $RuntimeRoot "picohrdl.dll"

if ((Test-Path -LiteralPath $Tc08Dll) -and
    (Test-Path -LiteralPath $HrdlDll)) {
    Write-Host "[PASS] Pico TC-08 and ADC-20/24 runtimes already installed."
    Write-Host "       $RuntimeRoot"
    exit 0
}

New-Item -ItemType Directory -Path $VendorRoot -Force | Out-Null

$WorkRoot = Join-Path $ProjectRoot "_bootstrap_pico"
$InstallerPath = Join-Path $WorkRoot "PicoSDK_x64.exe"
$InstallRoot = Join-Path $WorkRoot "installed"

if (Test-Path -LiteralPath $WorkRoot) {
    Remove-Item -LiteralPath $WorkRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $WorkRoot -Force | Out-Null
New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$MetadataUri = "https://www.picotech.com/downloads/_lightbox/pico-software-development-kit-64bit"

Write-Host "Finding the current official 64-bit PicoSDK installer..."
$Page = Invoke-WebRequest -Uri $MetadataUri -UseBasicParsing

$DownloadUri = $null

# PowerShell 5.1 may or may not populate Links when UseBasicParsing is used,
# so check both the parsed links and the raw HTML.
if ($Page.Links) {
    $Link = $Page.Links |
        Where-Object {
            $_.href -match "PicoSDK_x64_[0-9.]+\.exe(?:\?.*)?$"
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
    $Pattern = 'href=["'']([^"'']*PicoSDK_x64_[0-9.]+\.exe(?:\?[^"'']*)?)["'']'
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

if (-not $DownloadUri) {
    Fail @"
The current PicoSDK download link could not be found on:

  $MetadataUri

Pico may have changed the download page. The bootstrap did not modify the
existing Pico runtime.
"@
}

Write-Host "Downloading:"
Write-Host "  $DownloadUri"
Invoke-WebRequest `
    -Uri $DownloadUri `
    -UseBasicParsing `
    -OutFile $InstallerPath

if (-not (Test-Path -LiteralPath $InstallerPath)) {
    Fail "The PicoSDK installer was not downloaded."
}

$InstallerSize = (Get-Item -LiteralPath $InstallerPath).Length
if ($InstallerSize -lt 10000000) {
    Fail "The PicoSDK installer is unexpectedly small ($InstallerSize bytes)."
}

$InstallerHash = (
    Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256
).Hash

Write-Host "Downloaded SHA-256:"
Write-Host "  $InstallerHash"
Write-Host ""
Write-Host "Extracting the Pico runtime into the project..."
Write-Host "No system PATH change is made."

# Current PicoSDK Windows packages use an installer that accepts Inno Setup
# command-line switches. Install into a temporary project-local directory,
# then retain only runtime DLLs and licence/readme files.
$Arguments = @(
    "/VERYSILENT",
    "/SUPPRESSMSGBOXES",
    "/NORESTART",
    "/SP-",
    "/CURRENTUSER",
    "/DIR=$InstallRoot"
)

$Process = Start-Process `
    -FilePath $InstallerPath `
    -ArgumentList $Arguments `
    -Wait `
    -PassThru

if ($Process.ExitCode -ne 0) {
    Fail @"
The PicoSDK installer returned exit code $($Process.ExitCode).

The downloaded installer has been retained for inspection at:

  $InstallerPath

It can be run manually if Pico changes its unattended-install options.
"@
}

$Tc08Candidates = @(
    Get-ChildItem `
        -LiteralPath $InstallRoot `
        -Filter "usb_tc08.dll" `
        -File `
        -Recurse
)

$HrdlCandidates = @(
    Get-ChildItem `
        -LiteralPath $InstallRoot `
        -Filter "picohrdl.dll" `
        -File `
        -Recurse
)

if ($Tc08Candidates.Count -eq 0 -or $HrdlCandidates.Count -eq 0) {
    $DllNames = @(
        Get-ChildItem `
            -LiteralPath $InstallRoot `
            -Filter "*.dll" `
            -File `
            -Recurse |
        Select-Object -ExpandProperty Name -Unique |
        Sort-Object
    )

    Write-Host ""
    Write-Host "DLLs found by the Pico installer:"
    foreach ($Name in $DllNames) {
        Write-Host "  $Name"
    }

    Fail @"
The Pico installer completed, but the required runtime DLLs were not found.

Required:
  usb_tc08.dll
  picohrdl.dll

Temporary files were retained at:
  $WorkRoot
"@
}

if (Test-Path -LiteralPath $RuntimeRoot) {
    Remove-Item -LiteralPath $RuntimeRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null

# Copy all runtime DLLs from directories containing either requested data
# logger driver. This preserves dependencies shipped alongside the drivers.
$RuntimeDirectories = @(
    $Tc08Candidates.Directory.FullName
    $HrdlCandidates.Directory.FullName
) | Sort-Object -Unique

$Copied = @{}

foreach ($Directory in $RuntimeDirectories) {
    foreach ($Dll in Get-ChildItem -LiteralPath $Directory -Filter "*.dll" -File) {
        if (-not $Copied.ContainsKey($Dll.Name)) {
            Copy-Item `
                -LiteralPath $Dll.FullName `
                -Destination (Join-Path $RuntimeRoot $Dll.Name) `
                -Force
            $Copied[$Dll.Name] = $Dll.FullName
        }
    }
}

# Some dependencies may be one directory above the instrument-specific DLL.
foreach ($Directory in $RuntimeDirectories) {
    $Parent = Split-Path -Parent $Directory

    if ($Parent -and (Test-Path -LiteralPath $Parent)) {
        foreach ($Dll in Get-ChildItem -LiteralPath $Parent -Filter "*.dll" -File) {
            if (-not $Copied.ContainsKey($Dll.Name)) {
                Copy-Item `
                    -LiteralPath $Dll.FullName `
                    -Destination (Join-Path $RuntimeRoot $Dll.Name) `
                    -Force
                $Copied[$Dll.Name] = $Dll.FullName
            }
        }
    }
}

$Manifest = [ordered]@{
    source_page = $MetadataUri
    download_url = $DownloadUri
    installer_sha256 = $InstallerHash
    installed_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    runtime_files = @(
        Get-ChildItem -LiteralPath $RuntimeRoot -File |
        Select-Object -ExpandProperty Name |
        Sort-Object
    )
}

$Manifest |
    ConvertTo-Json -Depth 4 |
    Set-Content `
        -LiteralPath (Join-Path $VendorRoot "runtime-manifest.json") `
        -Encoding UTF8

if (-not (Test-Path -LiteralPath $Tc08Dll)) {
    Fail "usb_tc08.dll was not copied to the portable runtime."
}
if (-not (Test-Path -LiteralPath $HrdlDll)) {
    Fail "picohrdl.dll was not copied to the portable runtime."
}

Remove-Item -LiteralPath $WorkRoot -Recurse -Force

Write-Host "[PASS] Pico runtime support installed."
Write-Host "       TC-08:     $Tc08Dll"
Write-Host "       ADC-20/24: $HrdlDll"
Write-Host "       Runtime:   $RuntimeRoot"

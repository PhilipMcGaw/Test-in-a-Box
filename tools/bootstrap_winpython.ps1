[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot,

    # Python 3.13 is preferred. The script falls back to 3.12 if the selected
    # stable WinPython release does not contain a matching 64-bit Dot ZIP.
    [string[]] $PreferredPythonSeries = @("3.13", "3.12")
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Step {
    param([string] $Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Fail {
    param([string] $Message)
    Write-Error $Message
    exit 1
}

try {
    $ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
    $PythonTarget = Join-Path $ProjectRoot "python"
    $PythonExe = Join-Path $PythonTarget "python.exe"

    if (Test-Path -LiteralPath $PythonExe) {
        Write-Host "Portable Python already exists: $PythonExe"
        exit 0
    }

    if (Test-Path -LiteralPath $PythonTarget) {
        $existingItems = @(Get-ChildItem -LiteralPath $PythonTarget -Force)
        if ($existingItems.Count -gt 0) {
            Fail "The '$PythonTarget' folder exists but does not contain python.exe. Rename or remove that incomplete folder, then run setup again."
        }
    }

    $TempRoot = Join-Path $ProjectRoot "_winpython_bootstrap"
    $ArchivePath = Join-Path $TempRoot "winpython-dot.zip"
    $ExtractPath = Join-Path $TempRoot "extracted"

    if (Test-Path -LiteralPath $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path $TempRoot | Out-Null
    New-Item -ItemType Directory -Path $ExtractPath | Out-Null

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    Write-Step "Finding a stable WinPython release"

    $Headers = @{
        "Accept"     = "application/vnd.github+json"
        "User-Agent" = "Test-in-a-Box-bootstrap"
    }

    # Search several recent releases rather than relying only on /latest.
    # This allows a compatible 3.13 or 3.12 Dot build to be selected even
    # when the newest stable release has moved to a newer Python series.
    $ReleasesUri = "https://api.github.com/repos/winpython/winpython/releases?per_page=20"
    $Releases = Invoke-RestMethod -Uri $ReleasesUri -Headers $Headers

    $Asset = $null
    $SelectedRelease = $null

    foreach ($Series in $PreferredPythonSeries) {
        foreach ($Release in $Releases) {
            if ($Release.draft -or $Release.prerelease) {
                continue
            }

            # Dot is the small portable runtime. Exclude dotf and pre-release
            # asset names. Prefer ZIP so extraction is silent and predictable.
            $Pattern = "^WinPython64-$([regex]::Escape($Series))\.[0-9.]+dot\.zip$"
            $Match = @(
                $Release.assets |
                Where-Object { $_.name -match $Pattern }
            ) | Select-Object -First 1

            if ($null -ne $Match) {
                $Asset = $Match
                $SelectedRelease = $Release
                break
            }
        }

        if ($null -ne $Asset) {
            break
        }
    }

    if ($null -eq $Asset) {
        Fail "No stable 64-bit WinPython 3.13 or 3.12 Dot ZIP was found in the 20 most recent official releases."
    }

    Write-Host "Release: $($SelectedRelease.name)"
    Write-Host "Asset:   $($Asset.name)"
    Write-Host "Source:  $($Asset.browser_download_url)"

    Write-Step "Downloading WinPython"
    Invoke-WebRequest `
        -Uri $Asset.browser_download_url `
        -Headers $Headers `
        -OutFile $ArchivePath

    if (-not (Test-Path -LiteralPath $ArchivePath)) {
        Fail "The WinPython archive was not downloaded."
    }

    $DownloadedLength = (Get-Item -LiteralPath $ArchivePath).Length
    if ($DownloadedLength -lt 1000000) {
        Fail "The downloaded archive is unexpectedly small ($DownloadedLength bytes)."
    }

    # GitHub release assets may expose a digest such as "sha256:<hex>".
    # Verify it when available; otherwise continue with the official HTTPS asset.
    if ($Asset.PSObject.Properties.Name -contains "digest" -and $Asset.digest) {
        if ($Asset.digest -match "^sha256:([0-9a-fA-F]{64})$") {
            Write-Step "Verifying SHA-256 digest"
            $ExpectedHash = $Matches[1].ToUpperInvariant()
            $ActualHash = (Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash
            if ($ActualHash -ne $ExpectedHash) {
                Fail "SHA-256 verification failed. Expected $ExpectedHash but received $ActualHash."
            }
            Write-Host "SHA-256 verified."
        }
    }

    Write-Step "Extracting WinPython"
    Expand-Archive -LiteralPath $ArchivePath -DestinationPath $ExtractPath -Force

    $PythonDirectories = @(
        Get-ChildItem -LiteralPath $ExtractPath -Directory -Recurse |
        Where-Object {
            $_.Name -match "^python-[0-9.]+\.amd64$" -and
            (Test-Path -LiteralPath (Join-Path $_.FullName "python.exe"))
        }
    )

    if ($PythonDirectories.Count -ne 1) {
        $Names = ($PythonDirectories | ForEach-Object { $_.FullName }) -join "; "
        Fail "Expected exactly one portable Python runtime in the WinPython archive, but found $($PythonDirectories.Count). $Names"
    }

    $SourcePython = $PythonDirectories[0].FullName
    Write-Host "Runtime: $SourcePython"

    if (Test-Path -LiteralPath $PythonTarget) {
        Remove-Item -LiteralPath $PythonTarget -Recurse -Force
    }

    Write-Step "Creating the project python folder"
    Move-Item -LiteralPath $SourcePython -Destination $PythonTarget

    if (-not (Test-Path -LiteralPath $PythonExe)) {
        Fail "python.exe was not found after extraction: $PythonExe"
    }

    Write-Step "Checking the portable runtime"
    & $PythonExe -c "import sys; print(sys.executable); print(sys.version)"
    if ($LASTEXITCODE -ne 0) {
        Fail "The extracted Python runtime could not be started."
    }

    Write-Step "Cleaning temporary files"
    Remove-Item -LiteralPath $TempRoot -Recurse -Force

    Write-Host ""
    Write-Host "Portable Python is ready:"
    Write-Host "  $PythonExe"
    exit 0
}
catch {
    Write-Host ""
    Write-Host "WinPython bootstrap failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Temporary files were left in '_winpython_bootstrap' for inspection."
    exit 1
}

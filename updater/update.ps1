[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot,

    [Parameter(Mandatory = $true)]
    [ValidateSet("stable", "development")]
    [string] $Channel
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)

function Write-Step {
    param([string] $Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Fail {
    param([string] $Message)
    throw $Message
}

function Invoke-Robocopy {
    param(
        [string] $Source,
        [string] $Destination,
        [string[]] $ExtraArguments
    )

    $Arguments = @(
        $Source,
        $Destination,
        "/E",
        "/R:2",
        "/W:1",
        "/NFL",
        "/NDL",
        "/NJH",
        "/NJS",
        "/NP"
    ) + $ExtraArguments

    & robocopy.exe @Arguments | Out-Host
    $Code = $LASTEXITCODE

    # Robocopy exit codes 0-7 are success/informational.
    if ($Code -ge 8) {
        Fail "Robocopy failed with exit code $Code."
    }
}

function Get-FinalUri {
    param([string] $Uri)

    $Response = Invoke-WebRequest `
        -Uri $Uri `
        -UseBasicParsing `
        -MaximumRedirection 10

    return $Response.BaseResponse.ResponseUri.AbsoluteUri
}

function Get-LatestStableTag {
    param(
        [string] $Owner,
        [string] $Repository
    )

    $LatestReleaseUri = (
        "https://github.com/$Owner/$Repository/releases/latest"
    )

    try {
        $FinalUri = Get-FinalUri -Uri $LatestReleaseUri

        if ($FinalUri -match "/releases/tag/([^/?#]+)") {
            return [System.Uri]::UnescapeDataString($Matches[1])
        }
    }
    catch {
        Write-Host "[INFO] Latest release lookup did not return a release."
    }

    Write-Host "[INFO] No published release found; checking repository tags."

    $TagsFeedUri = (
        "https://github.com/$Owner/$Repository/tags.atom"
    )

    try {
        $FeedText = (
            Invoke-WebRequest `
                -Uri $TagsFeedUri `
                -UseBasicParsing
        ).Content

        [xml] $Feed = $FeedText
        $Namespace = New-Object System.Xml.XmlNamespaceManager(
            $Feed.NameTable
        )
        $Namespace.AddNamespace(
            "atom",
            "http://www.w3.org/2005/Atom"
        )

        $FirstEntry = $Feed.SelectSingleNode(
            "//atom:entry[1]",
            $Namespace
        )

        if ($null -eq $FirstEntry) {
            return $null
        }

        $TitleNode = $FirstEntry.SelectSingleNode(
            "atom:title",
            $Namespace
        )

        if ($null -eq $TitleNode) {
            return $null
        }

        $Tag = $TitleNode.InnerText.Trim()

        if ($Tag) {
            return $Tag
        }
    }
    catch {
        Write-Host "[INFO] Tag feed lookup failed: $($_.Exception.Message)"
    }

    return $null
}

function Get-ArchiveSourceRoot {
    param([string] $ExtractRoot)

    $Candidates = @(
        Get-ChildItem -LiteralPath $ExtractRoot -Directory |
        Where-Object {
            (Test-Path -LiteralPath (
                Join-Path $_.FullName "requirements.txt"
            )) -and
            (Test-Path -LiteralPath (
                Join-Path $_.FullName "tiab"
            )) -and
            (Test-Path -LiteralPath (
                Join-Path $_.FullName "webapp"
            ))
        }
    )

    if ($Candidates.Count -ne 1) {
        Fail (
            "Expected exactly one Test in a Box source folder in the " +
            "downloaded archive, but found $($Candidates.Count)."
        )
    }

    return $Candidates[0].FullName
}

function Read-CurrentState {
    param([string] $Root)

    $StatePath = Join-Path $Root ".update-state.json"

    if (-not (Test-Path -LiteralPath $StatePath)) {
        return $null
    }

    try {
        return Get-Content -LiteralPath $StatePath -Raw |
            ConvertFrom-Json
    }
    catch {
        return $null
    }
}

try {
    $ConfigPath = Join-Path $ProjectRoot "updater\update_config.json"

    if (-not (Test-Path -LiteralPath $ConfigPath)) {
        Fail "Updater configuration is missing: $ConfigPath"
    }

    $Config = Get-Content -LiteralPath $ConfigPath -Raw |
        ConvertFrom-Json

    $Owner = [string] $Config.repository_owner
    $Repository = [string] $Config.repository_name
    $DevelopmentBranch = [string] $Config.development_branch

    if (-not $Owner -or -not $Repository -or -not $DevelopmentBranch) {
        Fail "Updater repository configuration is incomplete."
    }

    Write-Host ""
    Write-Host "Test in a Box Updater"
    Write-Host "====================="
    Write-Host "Channel:    $Channel"
    Write-Host "Repository: $Owner/$Repository"
    Write-Host "Project:    $ProjectRoot"

    $CurrentState = Read-CurrentState -Root $ProjectRoot

    if ($null -ne $CurrentState) {
        Write-Host "Installed:  $($CurrentState.channel) / $($CurrentState.ref)"
    }
    else {
        Write-Host "Installed:  unknown (first managed update)"
    }

    if ($Channel -eq "stable") {
        Write-Step "Resolving the stable version"
        $Ref = Get-LatestStableTag `
            -Owner $Owner `
            -Repository $Repository

        if (-not $Ref) {
            Fail @"
No stable update is available.

The repository has neither a published GitHub release nor a discoverable tag.
Create a release or a version tag, or use the Development channel.
"@
        }

        $ArchiveUri = (
            "https://codeload.github.com/$Owner/$Repository/zip/refs/tags/" +
            [System.Uri]::EscapeDataString($Ref)
        )
    }
    else {
        $Ref = $DevelopmentBranch
        $ArchiveUri = (
            "https://codeload.github.com/$Owner/$Repository/zip/refs/heads/" +
            [System.Uri]::EscapeDataString($DevelopmentBranch)
        )
    }

    Write-Host "Selected:   $Channel / $Ref"
    Write-Host ""
    Write-Host "The Test in a Box application must be closed before updating."
    Write-Host "Local Python, vendor files, logs, runs, results, sequences and"
    Write-Host "webapp/config.json will be preserved."
    Write-Host ""

    $Confirmation = Read-Host "Continue with this update? [Y/N]"
    if ($Confirmation -notmatch "^[Yy]$") {
        Write-Host "Update cancelled."
        exit 0
    }

    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $WorkRoot = Join-Path $ProjectRoot "_update_work"
    $DownloadPath = Join-Path $WorkRoot "source.zip"
    $ExtractPath = Join-Path $WorkRoot "extracted"
    $PreservePath = Join-Path $WorkRoot "preserved"
    $BackupRoot = Join-Path (
        Join-Path $ProjectRoot "_update_backups"
    ) $Timestamp

    if (Test-Path -LiteralPath $WorkRoot) {
        Remove-Item -LiteralPath $WorkRoot -Recurse -Force
    }

    New-Item -ItemType Directory -Path $WorkRoot | Out-Null
    New-Item -ItemType Directory -Path $ExtractPath | Out-Null
    New-Item -ItemType Directory -Path $PreservePath | Out-Null
    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

    Write-Step "Downloading update"
    Write-Host $ArchiveUri

    Invoke-WebRequest `
        -Uri $ArchiveUri `
        -UseBasicParsing `
        -OutFile $DownloadPath

    if (-not (Test-Path -LiteralPath $DownloadPath)) {
        Fail "The update archive was not downloaded."
    }

    if ((Get-Item -LiteralPath $DownloadPath).Length -lt 10000) {
        Fail "The downloaded update archive is unexpectedly small."
    }

    Write-Step "Extracting and validating update"
    Expand-Archive `
        -LiteralPath $DownloadPath `
        -DestinationPath $ExtractPath `
        -Force

    $SourceRoot = Get-ArchiveSourceRoot -ExtractRoot $ExtractPath
    Write-Host "Source: $SourceRoot"

    Write-Step "Preserving local configuration"

    foreach ($RelativeFile in $Config.preserve_files) {
        $SourceFile = Join-Path $ProjectRoot $RelativeFile

        if (Test-Path -LiteralPath $SourceFile) {
            $SavedFile = Join-Path $PreservePath $RelativeFile
            $SavedParent = Split-Path -Parent $SavedFile
            New-Item -ItemType Directory -Path $SavedParent -Force |
                Out-Null
            Copy-Item `
                -LiteralPath $SourceFile `
                -Destination $SavedFile `
                -Force
            Write-Host "[PRESERVE] $RelativeFile"
        }
    }

    Write-Step "Creating application backup"

    $ExcludedDirectories = @(
        "python",
        "vendor",
        "logs",
        "runs",
        "results",
        "sequences",
        "_update_backups",
        "_update_work",
        ".git"
    )

    $BackupArguments = @("/XD") + (
        $ExcludedDirectories |
        ForEach-Object { Join-Path $ProjectRoot $_ }
    )

    Invoke-Robocopy `
        -Source $ProjectRoot `
        -Destination $BackupRoot `
        -ExtraArguments $BackupArguments

    Write-Host "Backup: $BackupRoot"

    Write-Step "Installing update"

    # Preserve the current updater if the downloaded source predates it.
    $UpdateBatBackup = Join-Path $PreservePath "update.bat"
    $UpdaterBackup = Join-Path $PreservePath "updater"

    if (Test-Path -LiteralPath (Join-Path $ProjectRoot "update.bat")) {
        Copy-Item `
            -LiteralPath (Join-Path $ProjectRoot "update.bat") `
            -Destination $UpdateBatBackup `
            -Force
    }

    if (Test-Path -LiteralPath (Join-Path $ProjectRoot "updater")) {
        Copy-Item `
            -LiteralPath (Join-Path $ProjectRoot "updater") `
            -Destination $UpdaterBackup `
            -Recurse `
            -Force
    }

    $MirrorArguments = @(
        "/MIR",
        "/XD",
        "python",
        "vendor",
        "logs",
        "runs",
        "results",
        "sequences",
        "_update_backups",
        "_update_work",
        ".git",
        "updater",
        "/XF",
        "update.bat"
    )

    try {
        Invoke-Robocopy `
            -Source $SourceRoot `
            -Destination $ProjectRoot `
            -ExtraArguments $MirrorArguments
    }
    catch {
        Write-Host ""
        Write-Host "Update copy failed. Restoring application backup..."
        Invoke-Robocopy `
            -Source $BackupRoot `
            -Destination $ProjectRoot `
            -ExtraArguments @("/E")
        throw
    }

    # Install the newer updater when it exists in the downloaded source.
    $DownloadedUpdater = Join-Path $SourceRoot "updater"
    $DownloadedUpdateBat = Join-Path $SourceRoot "update.bat"

    if (Test-Path -LiteralPath $DownloadedUpdater) {
        if (Test-Path -LiteralPath (Join-Path $ProjectRoot "updater")) {
            Remove-Item `
                -LiteralPath (Join-Path $ProjectRoot "updater") `
                -Recurse `
                -Force
        }

        Copy-Item `
            -LiteralPath $DownloadedUpdater `
            -Destination (Join-Path $ProjectRoot "updater") `
            -Recurse `
            -Force
    }
    elseif (Test-Path -LiteralPath $UpdaterBackup) {
        Copy-Item `
            -LiteralPath $UpdaterBackup `
            -Destination (Join-Path $ProjectRoot "updater") `
            -Recurse `
            -Force
    }

    if (Test-Path -LiteralPath $DownloadedUpdateBat) {
        Copy-Item `
            -LiteralPath $DownloadedUpdateBat `
            -Destination (Join-Path $ProjectRoot "update.bat") `
            -Force
    }
    elseif (Test-Path -LiteralPath $UpdateBatBackup) {
        Copy-Item `
            -LiteralPath $UpdateBatBackup `
            -Destination (Join-Path $ProjectRoot "update.bat") `
            -Force
    }

    foreach ($RelativeFile in $Config.preserve_files) {
        $SavedFile = Join-Path $PreservePath $RelativeFile

        if (Test-Path -LiteralPath $SavedFile) {
            $DestinationFile = Join-Path $ProjectRoot $RelativeFile
            $DestinationParent = Split-Path -Parent $DestinationFile

            New-Item `
                -ItemType Directory `
                -Path $DestinationParent `
                -Force |
                Out-Null

            Copy-Item `
                -LiteralPath $SavedFile `
                -Destination $DestinationFile `
                -Force
        }
    }

    $State = [ordered]@{
        channel = $Channel
        ref = $Ref
        repository = "$Owner/$Repository"
        updated_at = (Get-Date).ToString("o")
        backup = $BackupRoot
    }

    $State |
        ConvertTo-Json |
        Set-Content `
            -LiteralPath (Join-Path $ProjectRoot ".update-state.json") `
            -Encoding UTF8

    Remove-Item -LiteralPath $WorkRoot -Recurse -Force

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "                    Update Complete"
    Write-Host "============================================================"
    Write-Host ""
    Write-Host "Channel: $Channel"
    Write-Host "Version: $Ref"
    Write-Host "Backup:  $BackupRoot"
    Write-Host ""
    Write-Host "Your local Python runtime, vendor files and test data were"
    Write-Host "preserved."
    Write-Host ""

    $BootstrapPath = Join-Path $ProjectRoot "bootstrap.bat"

    if (Test-Path -LiteralPath $BootstrapPath) {
        $RunBootstrap = Read-Host (
            "Run bootstrap now to update dependencies? [Y/N]"
        )

        if ($RunBootstrap -match "^[Yy]$") {
            Start-Process -FilePath $BootstrapPath
        }
    }
    else {
        Write-Host "bootstrap.bat was not found; dependency update was skipped."
    }

    exit 0
}
catch {
    Write-Host ""
    Write-Host "Update failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Any completed backup is kept under _update_backups."
    exit 1
}

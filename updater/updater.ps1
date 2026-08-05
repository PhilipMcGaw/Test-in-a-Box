[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ProjectRoot = [IO.Path]::GetFullPath($ProjectRoot)
$Action = $env:TIAB_UPDATE_ACTION

function Step([string] $Text) {
    Write-Host ""
    Write-Host "==> $Text"
}

function Fail([string] $Text) {
    throw $Text
}

function Copy-Tree(
    [string] $Source,
    [string] $Destination,
    [string[]] $Extra
) {
    $Args = @(
        $Source, $Destination, "/E", "/R:2", "/W:1",
        "/NFL", "/NDL", "/NJH", "/NJS", "/NP"
    ) + $Extra

    & robocopy.exe @Args | Out-Host
    if ($LASTEXITCODE -ge 8) {
        Fail "Robocopy failed with exit code $LASTEXITCODE."
    }
}

function Read-Config {
    $Path = Join-Path $ProjectRoot "updater\updater_config.json"
    if (-not (Test-Path -LiteralPath $Path)) {
        Fail "Updater configuration is missing: $Path"
    }
    return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Get-LatestStableTag([string] $Owner, [string] $Repo) {
    try {
        $Response = Invoke-WebRequest `
            -Uri "https://github.com/$Owner/$Repo/releases/latest" `
            -UseBasicParsing `
            -MaximumRedirection 10
        $Final = $Response.BaseResponse.ResponseUri.AbsoluteUri
        if ($Final -match "/releases/tag/([^/?#]+)") {
            return [Uri]::UnescapeDataString($Matches[1])
        }
    }
    catch {
        Write-Host "[INFO] No published release was resolved."
    }

    try {
        [xml] $Feed = (
            Invoke-WebRequest `
                -Uri "https://github.com/$Owner/$Repo/tags.atom" `
                -UseBasicParsing
        ).Content

        $Ns = New-Object Xml.XmlNamespaceManager($Feed.NameTable)
        $Ns.AddNamespace("atom", "http://www.w3.org/2005/Atom")
        $Node = $Feed.SelectSingleNode("//atom:entry[1]/atom:title", $Ns)
        if ($null -ne $Node) {
            return $Node.InnerText.Trim()
        }
    }
    catch {
        Write-Host "[INFO] No tag was resolved."
    }

    return $null
}

function Get-DevelopmentCommit([string] $Owner, [string] $Repo, [string] $Branch) {
    try {
        [xml] $Feed = (
            Invoke-WebRequest `
                -Uri "https://github.com/$Owner/$Repo/commits/$Branch.atom" `
                -UseBasicParsing
        ).Content

        $Ns = New-Object Xml.XmlNamespaceManager($Feed.NameTable)
        $Ns.AddNamespace("atom", "http://www.w3.org/2005/Atom")
        $Node = $Feed.SelectSingleNode("//atom:entry[1]/atom:id", $Ns)
        if ($null -ne $Node -and $Node.InnerText -match "Commit/([0-9a-fA-F]+)$") {
            return $Matches[1]
        }
    }
    catch {
        Write-Host "[INFO] Development commit identity is unavailable."
    }
    return "unknown"
}

function Find-SourceRoot([string] $ExtractPath) {
    $Candidates = @(
        Get-ChildItem -LiteralPath $ExtractPath -Directory -Recurse |
        Where-Object {
            (Test-Path (Join-Path $_.FullName "requirements.txt")) -and
            (Test-Path (Join-Path $_.FullName "tiab")) -and
            (Test-Path (Join-Path $_.FullName "webapp"))
        }
    ) | Sort-Object FullName -Unique

    if ($Candidates.Count -ne 1) {
        Fail "Expected one project root in the archive; found $($Candidates.Count)."
    }
    return $Candidates[0].FullName
}

function Invoke-Rollback($Config) {
    $BackupBase = Join-Path $ProjectRoot "_update_backups"
    $Backups = @(
        Get-ChildItem -LiteralPath $BackupBase -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending
    )

    if ($Backups.Count -eq 0) {
        Fail "No backups are available."
    }

    Write-Host ""
    Write-Host "Available backups"
    Write-Host "================="
    for ($Index = 0; $Index -lt $Backups.Count; $Index++) {
        Write-Host ("{0}. {1}" -f ($Index + 1), $Backups[$Index].Name)
    }

    $Choice = Read-Host "Select backup number"
    $Number = 0
    if (-not [int]::TryParse($Choice, [ref] $Number)) {
        Fail "Invalid backup selection."
    }
    if ($Number -lt 1 -or $Number -gt $Backups.Count) {
        Fail "Backup selection is out of range."
    }

    $Selected = $Backups[$Number - 1].FullName
    Step "Restoring $Selected"

    $Extra = @(
        "/MIR", "/XD",
        (Join-Path $ProjectRoot "python"),
        (Join-Path $ProjectRoot "vendor"),
        (Join-Path $ProjectRoot "logs"),
        (Join-Path $ProjectRoot "runs"),
        (Join-Path $ProjectRoot "results"),
        (Join-Path $ProjectRoot "sequences"),
        (Join-Path $ProjectRoot "_update_backups")
    )
    Copy-Tree $Selected $ProjectRoot $Extra

    Write-Host ""
    Write-Host "Rollback complete."
    exit 0
}

try {
    if ([string]::IsNullOrWhiteSpace($Action)) {
        Fail "No updater action was supplied."
    }

    $Action = $Action.Trim().ToLowerInvariant()
    if ($Action -notin @("stable", "development", "rollback")) {
        Fail "Unknown updater action: $Action"
    }

    $Config = Read-Config

    if ($Action -eq "rollback") {
        Invoke-Rollback $Config
    }

    $Owner = [string] $Config.repository_owner
    $Repo = [string] $Config.repository_name
    $Branch = [string] $Config.development_branch
    $UpdaterVersion = [string] $Config.updater_version

    Write-Host ""
    Write-Host "Test in a Box Updater V2"
    Write-Host "========================"
    Write-Host "Channel: $Action"
    Write-Host "Project: $ProjectRoot"

    if ($Action -eq "stable") {
        Step "Resolving stable version"
        $Ref = Get-LatestStableTag $Owner $Repo
        if (-not $Ref) {
            Fail @"
No stable version is published.

Create a GitHub release or version tag, or select Development.
"@
        }
        $Commit = "tag:$Ref"
        $Uri = "https://codeload.github.com/$Owner/$Repo/zip/refs/tags/$([Uri]::EscapeDataString($Ref))"
    }
    else {
        $Ref = $Branch
        $Commit = Get-DevelopmentCommit $Owner $Repo $Branch
        $Uri = "https://codeload.github.com/$Owner/$Repo/zip/refs/heads/$([Uri]::EscapeDataString($Branch))"
    }

    Write-Host "Ref:     $Ref"
    Write-Host "Commit:  $Commit"
    Write-Host ""
    Write-Host "Close Test in a Box before proceeding."
    $Confirm = Read-Host "Continue? [Y/N]"
    if ($Confirm -notmatch "^[Yy]$") {
        Write-Host "Update cancelled."
        exit 0
    }

    $Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $Work = Join-Path $ProjectRoot "_update_work"
    $Archive = Join-Path $Work "source.zip"
    $Extract = Join-Path $Work "extract"
    $Preserved = Join-Path $Work "preserved"
    $Backup = Join-Path $ProjectRoot "_update_backups\$Stamp-$Action"

    if (Test-Path $Work) {
        Remove-Item $Work -Recurse -Force
    }
    New-Item -ItemType Directory -Path $Extract -Force | Out-Null
    New-Item -ItemType Directory -Path $Preserved -Force | Out-Null
    New-Item -ItemType Directory -Path $Backup -Force | Out-Null

    Step "Downloading update"
    Invoke-WebRequest -Uri $Uri -UseBasicParsing -OutFile $Archive
    $ArchiveHash = (Get-FileHash $Archive -Algorithm SHA256).Hash

    Step "Extracting and validating"
    Expand-Archive $Archive $Extract -Force
    $Source = Find-SourceRoot $Extract

    Step "Preserving local files"
    foreach ($Relative in $Config.preserve_files) {
        $Local = Join-Path $ProjectRoot $Relative
        if (Test-Path $Local) {
            $Saved = Join-Path $Preserved $Relative
            New-Item -ItemType Directory -Path (Split-Path $Saved) -Force |
                Out-Null
            Copy-Item $Local $Saved -Force
        }
    }

    Step "Creating backup"
    $BackupExtra = @(
        "/XD",
        (Join-Path $ProjectRoot "python"),
        (Join-Path $ProjectRoot "vendor"),
        (Join-Path $ProjectRoot "logs"),
        (Join-Path $ProjectRoot "runs"),
        (Join-Path $ProjectRoot "results"),
        (Join-Path $ProjectRoot "sequences"),
        (Join-Path $ProjectRoot "_update_backups"),
        (Join-Path $ProjectRoot "_update_work"),
        (Join-Path $ProjectRoot ".git")
    )
    Copy-Tree $ProjectRoot $Backup $BackupExtra

    Step "Installing application files"
    $InstallExtra = @(
        "/MIR", "/XD",
        "python", "vendor", "logs", "runs", "results", "sequences",
        "_update_backups", "_update_work", ".git"
    )

    try {
        Copy-Tree $Source $ProjectRoot $InstallExtra
    }
    catch {
        Write-Host "Installation failed; restoring backup."
        Copy-Tree $Backup $ProjectRoot @("/MIR")
        throw
    }

    foreach ($Relative in $Config.preserve_files) {
        $Saved = Join-Path $Preserved $Relative
        if (Test-Path $Saved) {
            $Target = Join-Path $ProjectRoot $Relative
            New-Item -ItemType Directory -Path (Split-Path $Target) -Force |
                Out-Null
            Copy-Item $Saved $Target -Force
        }
    }

    $State = [ordered]@{
        updater_version = $UpdaterVersion
        channel = $Action
        ref = $Ref
        commit = $Commit
        archive_sha256 = $ArchiveHash
        repository = "$Owner/$Repo"
        updated_at = (Get-Date).ToUniversalTime().ToString("o")
        backup = $Backup
    }
    $State | ConvertTo-Json |
        Set-Content (Join-Path $ProjectRoot ".update-state.json") -Encoding UTF8

    Remove-Item $Work -Recurse -Force

    Step "Running bootstrap"
    $Bootstrap = Join-Path $ProjectRoot "bootstrap.bat"
    if (-not (Test-Path $Bootstrap)) {
        Fail "Update installed, but bootstrap.bat is missing."
    }

    $BootstrapProcess = Start-Process `
        -FilePath $Bootstrap `
        -Wait `
        -PassThru

    if ($BootstrapProcess.ExitCode -ne 0) {
        Fail "Bootstrap failed with exit code $($BootstrapProcess.ExitCode)."
    }

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "                Update Completed Successfully"
    Write-Host "============================================================"
    Write-Host "Channel: $Action"
    Write-Host "Ref:     $Ref"
    Write-Host "Commit:  $Commit"
    Write-Host "Backup:  $Backup"
    Write-Host ""

    $Launch = Read-Host "Launch Test in a Box now? [Y/N]"
    if ($Launch -match "^[Yy]$") {
        Start-Process (Join-Path $ProjectRoot "2_start_app.bat")
    }

    exit 0
}
catch {
    Write-Host ""
    Write-Host "Updater V2 failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

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

function Get-TiabProcesses {
    $Found = @{}
    $NormalRoot = $ProjectRoot.TrimEnd("\").ToLowerInvariant()

    # Find Python/CMD processes whose command line points at this repository.
    try {
        $Processes = Get-CimInstance Win32_Process -ErrorAction Stop |
            Where-Object {
                $CommandLine = [string] $_.CommandLine

                $CommandLine -and
                $CommandLine.ToLowerInvariant().Contains($NormalRoot) -and
                (
                    $CommandLine -match "webapp[\\/]+server\.py" -or
                    $CommandLine -match "uvicorn" -or
                    $CommandLine -match "2_start_app\.bat"
                )
            }

        foreach ($Process in $Processes) {
            $Found[[int] $Process.ProcessId] = [pscustomobject]@{
                ProcessId = [int] $Process.ProcessId
                Name = [string] $Process.Name
                CommandLine = [string] $Process.CommandLine
                Source = "project command line"
            }
        }
    }
    catch {
        Write-Host "[INFO] Process command-line inspection is unavailable."
    }

    # Also identify the process currently listening on the application port.
    $ListeningPids = @()

    if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
        try {
            $ListeningPids = @(
                Get-NetTCPConnection `
                    -LocalAddress "127.0.0.1" `
                    -LocalPort 8765 `
                    -State Listen `
                    -ErrorAction Stop |
                Select-Object -ExpandProperty OwningProcess -Unique
            )
        }
        catch {
            $ListeningPids = @()
        }
    }
    else {
        $NetstatLines = @(
            & netstat.exe -ano -p tcp 2>$null |
            Select-String -Pattern "127\.0\.0\.1:8765\s+.*LISTENING\s+(\d+)$"
        )

        foreach ($Line in $NetstatLines) {
            if ($Line.Line -match "LISTENING\s+(\d+)$") {
                $ListeningPids += [int] $Matches[1]
            }
        }
    }

    foreach ($ProcessId in $ListeningPids) {
        if ($Found.ContainsKey([int] $ProcessId)) {
            continue
        }

        try {
            $Process = Get-CimInstance `
                Win32_Process `
                -Filter "ProcessId = $ProcessId" `
                -ErrorAction Stop

            $Found[[int] $ProcessId] = [pscustomobject]@{
                ProcessId = [int] $ProcessId
                Name = [string] $Process.Name
                CommandLine = [string] $Process.CommandLine
                Source = "listening on 127.0.0.1:8765"
            }
        }
        catch {
            $Found[[int] $ProcessId] = [pscustomobject]@{
                ProcessId = [int] $ProcessId
                Name = "unknown"
                CommandLine = ""
                Source = "listening on 127.0.0.1:8765"
            }
        }
    }

    return @($Found.Values | Sort-Object ProcessId)
}


function Wait-ForTiabShutdown {
    while ($true) {
        $Running = @(Get-TiabProcesses)

        if ($Running.Count -eq 0) {
            Write-Host "[PASS] Test in a Box is not running."
            return
        }

        Write-Host ""
        Write-Host "Test in a Box is currently running."
        Write-Host "It must be closed before application files are updated."
        Write-Host ""

        foreach ($Process in $Running) {
            Write-Host ("  PID {0,-7} {1}" -f $Process.ProcessId, $Process.Name)
            Write-Host ("      Detected by: {0}" -f $Process.Source)

            if (-not [string]::IsNullOrWhiteSpace($Process.CommandLine)) {
                Write-Host ("      Command: {0}" -f $Process.CommandLine)
            }
        }

        Write-Host ""
        Write-Host "  [C] Check again after five seconds"
        Write-Host "  [F] Force close the detected Test in a Box process(es)"
        Write-Host "  [Q] Cancel the update"
        Write-Host ""

        $Selection = (Read-Host "Select [C/F/Q]").Trim().ToUpperInvariant()

        switch ($Selection) {
            "C" {
                Write-Host "Waiting for Test in a Box to close..."
                Start-Sleep -Seconds 5
            }

            "F" {
                Write-Host ""
                Write-Host "Force closing the detected Test in a Box process(es)..."

                foreach ($Process in $Running) {
                    try {
                        Stop-Process `
                            -Id $Process.ProcessId `
                            -Force `
                            -ErrorAction Stop

                        Write-Host (
                            "[PASS] Stopped PID {0} ({1})." -f
                            $Process.ProcessId,
                            $Process.Name
                        )
                    }
                    catch {
                        Fail (
                            "Could not stop PID {0}: {1}" -f
                            $Process.ProcessId,
                            $_.Exception.Message
                        )
                    }
                }

                $Deadline = (Get-Date).AddSeconds(10)

                do {
                    Start-Sleep -Milliseconds 500
                    $Remaining = @(Get-TiabProcesses)
                } while (
                    $Remaining.Count -gt 0 -and
                    (Get-Date) -lt $Deadline
                )

                if ($Remaining.Count -gt 0) {
                    Fail (
                        "Test in a Box is still running after the force-close " +
                        "request. Close it manually and run the updater again."
                    )
                }

                Write-Host "[PASS] Test in a Box has closed."
                return
            }

            "Q" {
                Write-Host "Update cancelled."
                exit 0
            }

            default {
                Write-Host "Please select C, F, or Q."
            }
        }
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
        (Join-Path $ProjectRoot "webapp\runs"),
        (Join-Path $ProjectRoot "webapp\results"),
        (Join-Path $ProjectRoot "webapp\sequences"),
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
    $BuildInfoPath = Join-Path $ProjectRoot "support\BUILD.json"
    if (Test-Path -LiteralPath $BuildInfoPath) {
        $BuildInfo = Get-Content -LiteralPath $BuildInfoPath -Raw |
            ConvertFrom-Json
        $UpdaterVersion = [string] $BuildInfo.updater_version
    }
    else {
        $UpdaterVersion = [string] $Config.updater_version
    }

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
    Step "Checking application state"
    Wait-ForTiabShutdown

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
        (Join-Path $ProjectRoot "webapp\runs"),
        (Join-Path $ProjectRoot "webapp\results"),
        (Join-Path $ProjectRoot "webapp\sequences"),
        (Join-Path $ProjectRoot "_update_backups"),
        (Join-Path $ProjectRoot "_update_work"),
        (Join-Path $ProjectRoot ".git")
    )
    Copy-Tree $ProjectRoot $Backup $BackupExtra

    Step "Installing application files"
    $InstallExtra = @(
        "/MIR", "/XD",
        "python", "vendor", "logs", "webapp\runs", "webapp\results", "webapp\sequences",
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

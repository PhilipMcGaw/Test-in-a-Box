param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot,

    [int] $ReadyTimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"

$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$PythonExe = Join-Path $ProjectRoot "python\python.exe"
$ReadyUrl = "http://127.0.0.1:8765/api/version"
$BrowserUrl = "http://127.0.0.1:8765"

if (-not (Test-Path -LiteralPath $PythonExe)) {
    Write-Host ""
    Write-Host "Could not find python.exe at:"
    Write-Host "  $PythonExe"
    Write-Host ""
    Write-Host "Run bootstrap.bat, or see docs\getting-started\WINDOWS.md."
    exit 1
}

Set-Location -LiteralPath $ProjectRoot

Write-Host "Starting Test in a Box..."
Write-Host "Keep this window open while you're using the app."
Write-Host "Close this window to stop the app."
Write-Host ""

# Start exactly one server process and keep it attached to this console.
$Server = Start-Process `
    -FilePath $PythonExe `
    -ArgumentList @("-m", "webapp.server") `
    -WorkingDirectory $ProjectRoot `
    -NoNewWindow `
    -PassThru

Write-Host "Waiting for server..."

$Deadline = (Get-Date).AddSeconds($ReadyTimeoutSeconds)
$Ready = $false

while ((Get-Date) -lt $Deadline) {
    if ($Server.HasExited) {
        Write-Host ""
        Write-Host (
            "ERROR: Test in a Box exited before the server became ready " +
            "(exit code $($Server.ExitCode))."
        )
        exit $Server.ExitCode
    }

    try {
        $Response = Invoke-WebRequest `
            -UseBasicParsing `
            -Uri $ReadyUrl `
            -TimeoutSec 2

        if ($Response.StatusCode -eq 200) {
            $Ready = $true
            break
        }
    }
    catch {
        # Normal while Uvicorn is still starting.
    }

    Start-Sleep -Milliseconds 250
}

if (-not $Ready) {
    Write-Host ""
    Write-Host (
        "ERROR: Server did not become ready within " +
        "$ReadyTimeoutSeconds seconds."
    )

    if (-not $Server.HasExited) {
        Stop-Process -Id $Server.Id -Force -ErrorAction SilentlyContinue
    }

    exit 1
}

Write-Host "Server ready. Opening browser..."
Start-Process $BrowserUrl

# Keep this launcher alive for the lifetime of the one server process so the
# original command window remains the application's console.
$Server.WaitForExit()
exit $Server.ExitCode

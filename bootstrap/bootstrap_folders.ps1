[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)


$Folders = @(
    "logs",
    "webapp\runs",
    "webapp\sequences",
    "vendor",
    "vendor\seeit",
    "vendor\pico",
    "vendor\pico\installer"
)

foreach ($Relative in $Folders) {
    $Path = Join-Path $ProjectRoot $Relative
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        Write-Host "[CREATE] $Relative"
    }
    else {
        Write-Host "[PASS]   $Relative"
    }
}

Write-Host "[PASS] Project folders are ready."

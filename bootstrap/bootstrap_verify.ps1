[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)


$PythonExe = Join-Path $ProjectRoot "python\python.exe"
$Checks = New-Object System.Collections.Generic.List[object]

function Add-Check(
    [string] $Name,
    [bool] $Passed,
    [string] $Details,
    [bool] $Required = $true
) {
    $Checks.Add([pscustomobject]@{
        Name = $Name
        Passed = $Passed
        Details = $Details
        Required = $Required
    })
}

Add-Check "Portable Python" (Test-Path -LiteralPath $PythonExe) $PythonExe

foreach ($Folder in @("logs", "runs", "sequences", "vendor", "vendor\seeit", "vendor\pico")) {
    $Path = Join-Path $ProjectRoot $Folder
    Add-Check "Folder: $Folder" (Test-Path -LiteralPath $Path) $Path
}

$DllPath = Join-Path $ProjectRoot "vendor\seeit\usb_relay_device.dll"
Add-Check "Seeit native DLL" (Test-Path -LiteralPath $DllPath) `
    "Optional Windows-only component" $false

if (Test-Path -LiteralPath $PythonExe) {
    Push-Location $ProjectRoot
    try {
        & $PythonExe -c "import fastapi, uvicorn, pydantic, serial, pyvisa; import tiab; print('core imports OK')" *> $null
        Add-Check "Core Python imports" ($LASTEXITCODE -eq 0) `
            "fastapi, uvicorn, pydantic, pyserial, pyvisa, tiab"

        & $PythonExe -m pip check *> $null
        Add-Check "Dependency consistency" ($LASTEXITCODE -eq 0) "pip check"

        # Missing Pico native libraries are an expected optional result.
        # Windows PowerShell 5.1 otherwise converts Python stderr into a
        # terminating NativeCommandError while ErrorActionPreference is Stop.
        $PreviousErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"

        try {
            & $PythonExe `
                -c "from picosdk.usbtc08 import usbtc08; from picosdk.picohrdl import picohrdl" `
                1>$null `
                2>$null

            $PicoProbeExitCode = $LASTEXITCODE
        }
        finally {
            $ErrorActionPreference = $PreviousErrorActionPreference
        }

        Add-Check "Pico runtime support" ($PicoProbeExitCode -eq 0) `
            "Optional TC-08 and ADC-20/24 runtime" $false

        & $PythonExe -m compileall -q tiab webapp *> $null
        Add-Check "Python syntax" ($LASTEXITCODE -eq 0) "compileall tiab webapp"
    }
    finally {
        Pop-Location
    }
}
else {
    Add-Check "Core Python imports" $false "Python unavailable"
    Add-Check "Dependency consistency" $false "Python unavailable"
    Add-Check "Python syntax" $false "Python unavailable"
}

Write-Host ""
Write-Host "Bootstrap Report"
Write-Host "================"

foreach ($Check in $Checks) {
    if ($Check.Passed) {
        $Status = "PASS"
    }
    elseif ($Check.Required) {
        $Status = "FAIL"
    }
    else {
        $Status = "INFO"
    }

    Write-Host ("{0,-28} {1,-5} {2}" -f $Check.Name, $Status, $Check.Details)
}

$RequiredFailures = @($Checks | Where-Object { $_.Required -and -not $_.Passed })

if ($RequiredFailures.Count -gt 0) {
    throw "$($RequiredFailures.Count) required bootstrap verification check(s) failed."
}

Write-Host ""
Write-Host "[PASS] Test in a Box is ready to start."

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ProjectRoot
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)


$VendorRoot = Join-Path $ProjectRoot "vendor"
$SeeitRoot = Join-Path $VendorRoot "seeit"
$DllCandidates = @(
    (Join-Path $SeeitRoot "usb_relay_device.dll"),
    (Join-Path $VendorRoot "usb_relay_device.dll")
)

if (-not (Test-Path -LiteralPath $VendorRoot)) {
    New-Item -ItemType Directory -Path $VendorRoot -Force | Out-Null
}
if (-not (Test-Path -LiteralPath $SeeitRoot)) {
    New-Item -ItemType Directory -Path $SeeitRoot -Force | Out-Null
}

$FoundDll = $DllCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if ($null -ne $FoundDll) {
    Write-Host "[PASS] Seeit native USB relay DLL found:"
    Write-Host "       $FoundDll"
}
else {
    Write-Host "[INFO] Optional Seeit native USB relay DLL not found."
    Write-Host "       Native USBB relay support will be unavailable."
    Write-Host "       Place the licensed matching DLL at:"
    Write-Host "       $SeeitRoot\usb_relay_device.dll"
}

Write-Host "[PASS] Vendor component check completed."

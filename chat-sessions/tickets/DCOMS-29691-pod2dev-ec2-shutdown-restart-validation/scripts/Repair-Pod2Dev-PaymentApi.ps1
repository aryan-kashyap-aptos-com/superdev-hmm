# Manual repair: create pod2-dev-payment IIS site on API server.
# Run on: oms-pod2-dev-api (via SSM as domain admin context if possible)
# Prerequisite: \\omspod.aptos.com\pod2-dev\dev\payment must be reachable and contain PaymentApi files.

$ErrorActionPreference = 'Stop'

$siteName = 'pod2-dev-payment'
$physicalPath = '\\omspod.aptos.com\pod2-dev\dev\payment'
$hostHeader = 'oms-pod2-dev-paymentapi.dev.eom.aptos.io'

Import-Module WebAdministration

Write-Output "Checking payment UNC: $physicalPath"
if (-not (Test-Path $physicalPath)) {
    throw "Payment UNC not reachable: $physicalPath. Fix DFS/content deploy first."
}

$webConfig = Join-Path $physicalPath 'Web.config'
if (-not (Test-Path $webConfig)) {
    throw "Payment Web.config not found under $physicalPath. Deploy payment binaries first."
}

$existing = Get-Website -Name $siteName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Output "Site $siteName already exists (state: $($existing.State)). Updating bindings/path."
    Set-ItemProperty "IIS:\Sites\$siteName" -Name physicalPath -Value $physicalPath
} else {
    if (-not (Test-Path "IIS:\AppPools\$siteName")) {
        New-Item IIS:\AppPools\$siteName | Out-Null
    }
    New-Item IIS:\Sites\$siteName -physicalPath $physicalPath -bindings @{protocol='http';bindingInformation="*:80:$hostHeader"} | Out-Null
    Set-ItemProperty "IIS:\Sites\$siteName" -Name applicationPool -Value $siteName
    Set-WebConfigurationProperty -PSPath "IIS:\Sites\$siteName" -Filter '/system.webServer/directoryBrowse' -Name 'enabled' -Value $false
}

# Ensure host-header binding exists
$bindings = Get-WebBinding -Name $siteName
$hasBinding = $bindings | Where-Object { $_.bindingInformation -like "*:$hostHeader" }
if (-not $hasBinding) {
    New-WebBinding -Name $siteName -Protocol http -HostHeader $hostHeader -Port 80 | Out-Null
}

Start-Website -Name $siteName
Write-Output "Site $siteName started."

Write-Output '=== Verification ==='
Get-Website -Name $siteName | Format-Table Name,State,PhysicalPath -AutoSize | Out-String | Write-Output
Get-WebBinding -Name $siteName | Format-Table protocol,bindingInformation -AutoSize | Out-String | Write-Output

try {
    $resp = Invoke-WebRequest -Uri "http://localhost/api/payment/v1" -Headers @{ Host = $hostHeader } -UseBasicParsing -TimeoutSec 20
    Write-Output "Local probe status: $($resp.StatusCode)"
} catch {
    Write-Output "Local probe error: $($_.Exception.Message)"
}

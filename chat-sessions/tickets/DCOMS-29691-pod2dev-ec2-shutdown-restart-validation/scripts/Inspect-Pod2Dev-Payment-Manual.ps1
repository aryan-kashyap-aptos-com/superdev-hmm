$ErrorActionPreference = 'Continue'

Write-Output '=== Hostname ==='
Write-Output $env:COMPUTERNAME

Write-Output '=== Local dev folders ==='
$paths = @('D:\dev', 'D:\content\dev', 'D:\dev\payment', 'D:\content\dev\payment')
foreach ($p in $paths) {
    if (Test-Path $p) {
        Write-Output "EXISTS: $p"
        Get-ChildItem $p -ErrorAction SilentlyContinue | Select-Object -First 10 Name,Mode,LastWriteTime | Format-Table -AutoSize | Out-String | Write-Output
    } else {
        Write-Output "MISSING: $p"
    }
}

Write-Output '=== DFS UNC probes ==='
$uncs = @(
    '\\omspod.aptos.com\pod2-dev\dev',
    '\\omspod.aptos.com\pod2-dev\dev\api',
    '\\omspod.aptos.com\pod2-dev\dev\payment',
    '\\omspod.aptos.com\pod2-dev\dev\sm'
)
foreach ($unc in $uncs) {
    try {
        if (Test-Path $unc) {
            Write-Output "REACHABLE: $unc"
            Get-ChildItem $unc -ErrorAction Stop | Select-Object -First 5 Name | Format-Table -AutoSize | Out-String | Write-Output
        } else {
            Write-Output "NOT FOUND: $unc"
        }
    } catch {
        Write-Output "ERROR: $unc -> $($_.Exception.Message)"
    }
}

Write-Output '=== SMB shares (content server) ==='
Get-SmbShare -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'dev|content|payment' } | Format-Table Name,Path,Description -AutoSize | Out-String | Write-Output

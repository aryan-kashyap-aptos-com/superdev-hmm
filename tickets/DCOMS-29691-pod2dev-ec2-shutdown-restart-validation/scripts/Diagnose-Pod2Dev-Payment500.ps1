$ErrorActionPreference = 'Continue'

Write-Output '=== Payment web.config key settings ==='
$paymentRoot = 'D:\content\dev\payment'
$files = @(
    (Join-Path $paymentRoot 'web.config'),
    (Join-Path $paymentRoot 'web.appsettings.config'),
    (Join-Path $paymentRoot 'web.bindingclients.config')
)
foreach ($f in $files) {
    if (Test-Path $f) {
        Write-Output "--- $f ---"
        Select-String -Path $f -Pattern 'connectionString|appSettings|endpoint|parameter|redis|rds|postgres|oms|key|secret|payment' -CaseSensitive:$false |
            Select-Object -First 40 |
            ForEach-Object { Write-Output $_.Line.Trim() }
    } else {
        Write-Output "MISSING: $f"
    }
}

Write-Output '=== Payment log folders ==='
$logCandidates = @(
    'D:\content\dev\payment\logs',
    'D:\logs\payment',
    'D:\logs',
    'C:\inetpub\logs\LogFiles\W3SVC*'
)
foreach ($c in $logCandidates) {
    if (Test-Path $c) {
        Write-Output "LOG PATH: $c"
        Get-ChildItem $c -Recurse -File -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 5 FullName,LastWriteTime,Length |
            Format-Table -AutoSize | Out-String | Write-Output
    }
}

Write-Output '=== Recent Application events (last 20) ==='
Get-EventLog -LogName Application -Newest 20 -ErrorAction SilentlyContinue |
    Where-Object { $_.EntryType -eq 'Error' } |
    Select-Object TimeGenerated,Source,EventID,Message |
    Format-List | Out-String | Write-Output

# eom-core shared dev: find ShopLogic React static (SM + content deploy paths).
$searchRoots = @(
    'D:\content',
    'D:\OMS',
    'C:\OMS',
    'C:\inetpub',
    'E:\content'
)
Write-Host "=== Websites ==="
Get-Website | Select-Object Name, State, PhysicalPath | Format-Table -AutoSize

Write-Host "=== mainReact.js under search roots ==="
$hits = @()
foreach ($root in $searchRoots) {
    if (-not (Test-Path -LiteralPath $root)) { continue }
    Get-ChildItem -LiteralPath $root -Recurse -Filter mainReact.js -ErrorAction SilentlyContinue | ForEach-Object { $hits += $_ }
}
if ($hits.Count -eq 0) {
    Write-Host 'No mainReact.js found'
} else {
    foreach ($f in $hits) {
        Write-Host "FILE $($f.FullName) size=$($f.Length) utc=$($f.LastWriteTimeUtc)"
        $dir = $f.DirectoryName
        $chunks = @(Get-ChildItem -LiteralPath $dir -Filter '*chunk*.js' -ErrorAction SilentlyContinue)
        Write-Host "  chunks=$($chunks.Count)"
        $raw = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction SilentlyContinue
        if ($raw -match 'OdxFeedMonitorApp') { Write-Host '  has: OdxFeedMonitorApp' } else { Write-Host '  NO OdxFeedMonitorApp in bundle' }
        if ($raw -match 'odxFeedMonitor') { Write-Host '  has: odxFeedMonitor' } else { Write-Host '  NO odxFeedMonitor string' }
    }
}

Write-Host "=== OdxFeedMonitor.aspx ==="
foreach ($root in $searchRoots) {
    if (-not (Test-Path -LiteralPath $root)) { continue }
    Get-ChildItem -LiteralPath $root -Recurse -Filter OdxFeedMonitor.aspx -ErrorAction SilentlyContinue |
        Select-Object -First 5 FullName, LastWriteTimeUtc |
        ForEach-Object { Write-Host "ASPX $($_.FullName) utc=$($_.LastWriteTimeUtc)" }
}

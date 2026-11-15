$jsDir = 'D:\content\dev\poddev\sm\static\js'
$cssDir = 'D:\content\dev\poddev\sm\static\css'
Write-Host "HOST $env:COMPUTERNAME"
if (-not (Test-Path -LiteralPath $jsDir)) {
    Write-Host "MISSING $jsDir"
    exit 1
}
Write-Host "OK $jsDir"
Get-ChildItem -LiteralPath $jsDir -File | Sort-Object LastWriteTimeUtc -Descending |
    Select-Object Name, Length, LastWriteTimeUtc | Format-Table -AutoSize
$main = Get-ChildItem -LiteralPath $jsDir -Filter mainReact.js -ErrorAction SilentlyContinue | Select-Object -First 1
if ($main) {
    Write-Host "mainReact.js size=$($main.Length) utc=$($main.LastWriteTimeUtc)"
    $raw = Get-Content -LiteralPath $main.FullName -Raw
    if ($raw -match 'OdxFeedMonitorApp') { Write-Host 'bundle: OdxFeedMonitorApp present' } else { Write-Host 'bundle: NO OdxFeedMonitorApp' }
    if ($raw -match 'odxFeedMonitor') { Write-Host 'bundle: odxFeedMonitor string present' } else { Write-Host 'bundle: NO odxFeedMonitor string' }
    if ($raw -match 'API connected') { Write-Host 'bundle: has API connected placeholder' }
}
if (Test-Path -LiteralPath $cssDir) {
    Get-ChildItem -LiteralPath $cssDir -Filter mainReact.css -ErrorAction SilentlyContinue |
        Select-Object Name, Length, LastWriteTimeUtc | Format-Table -AutoSize
}
$aspx = 'D:\content\dev\poddev\sm\backadmin\OdxFeedMonitor.aspx'
if (Test-Path -LiteralPath $aspx) {
    $a = Get-Item -LiteralPath $aspx
    Write-Host "ASPX exists utc=$($a.LastWriteTimeUtc)"
} else {
    Write-Host "ASPX missing $aspx"
}

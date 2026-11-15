$roots = @(
    'C:\OMS',
    'D:\OMS',
    'C:\inetpub\wwwroot',
    'E:\OMS'
)
$found = @()
foreach ($root in $roots) {
    if (-not (Test-Path $root)) { continue }
    Get-ChildItem -Path $root -Recurse -Filter mainReact.js -ErrorAction SilentlyContinue | ForEach-Object { $found += $_ }
}
if ($found.Count -eq 0) {
    Write-Host 'mainReact.js not found under common OMS roots'
    exit 1
}
foreach ($f in $found) {
    Write-Host "FILE $($f.FullName) size=$($f.Length) utc=$($f.LastWriteTimeUtc)"
    $dir = $f.DirectoryName
    $chunks = Get-ChildItem $dir -Filter '*chunk*.js' -ErrorAction SilentlyContinue
    Write-Host "  chunks: $($chunks.Count)"
    $content = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction SilentlyContinue
    if ($content -match 'OdxFeedMonitor') { Write-Host '  contains: OdxFeedMonitor string' } else { Write-Host '  missing: OdxFeedMonitor string in mainReact.js' }
    if ($content -match 'odxFeedMonitor') { Write-Host '  contains: odxFeedMonitor string' } else { Write-Host '  missing: odxFeedMonitor string in mainReact.js' }
    if ($content -match 'API connected') { Write-Host '  contains: API connected placeholder text' }
    if ($content -match 'Summary rows') { Write-Host '  contains: Summary rows text' }
}
$aspx = Get-ChildItem -Path C:\OMS, D:\OMS -Recurse -Filter OdxFeedMonitor.aspx -ErrorAction SilentlyContinue | Select-Object -First 3
foreach ($a in $aspx) { Write-Host "ASPX $($a.FullName) utc=$($a.LastWriteTimeUtc)" }

$ConnectorRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ConnectorRoot '.env'
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.*)$') { Set-Item -Path "Env:$($matches[1].Trim())" -Value $matches[2].Trim() }
}
$account = '82alj-w-QGSN-OFFBTv9Ew'
$h = @{ 'x-api-key' = $env:HARNESS_API_KEY; 'Harness-Account' = $account }
$exportDir = Join-Path $ConnectorRoot 'exports'
New-Item -ItemType Directory -Force -Path $exportDir | Out-Null

$orgs = Invoke-RestMethod -Uri "https://app.harness.io/ng/api/aggregate/organizations?accountIdentifier=$account&pageIndex=0&pageSize=5" -Headers $h
$projs = Invoke-RestMethod -Uri "https://app.harness.io/ng/api/aggregate/projects?accountIdentifier=$account&pageIndex=0&pageSize=100" -Headers $h

$orgs.data.content[0] | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $exportDir 'org-sample.json')
$projs.data.content | Where-Object { $_.projectResponse.name -match 'OMS' } | Select-Object -First 5 | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $exportDir 'project-oms-samples.json')

# flat project table
$projs.data.content | ForEach-Object {
    $p = $_.projectResponse.project
    if (-not $p) { $p = $_.projectResponse }
    if ($p) {
        [PSCustomObject]@{ org = $p.orgIdentifier; id = $p.identifier; name = $p.name }
    }
} | Where-Object { $_.name -match 'OMS|Development|Sitemanager|sitemanager' } |
    Format-Table -AutoSize | Out-String | Set-Content (Join-Path $exportDir 'project-table.txt')

Get-Content (Join-Path $exportDir 'project-table.txt')

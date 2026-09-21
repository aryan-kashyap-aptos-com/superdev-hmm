# Resolve Aptos OMS org + common project identifiers via Harness filter APIs.
$ErrorActionPreference = 'Stop'
$ConnectorRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ConnectorRoot '.env'

Get-Content -LiteralPath $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq '' -or $line.StartsWith('#')) { return }
    $eq = $line.IndexOf('=')
    if ($eq -lt 1) { return }
    Set-Item -Path "Env:$($line.Substring(0, $eq).Trim())" -Value $line.Substring($eq + 1).Trim()
}

$m = [regex]::Match($env:HARNESS_API_KEY, '^pat\.([^.]+)\.')
$account = $m.Groups[1].Value
$headers = @{ 'x-api-key' = $env:HARNESS_API_KEY }

$orgFilter = @{
    filterType = 'Org'
    searchTerm = 'Aptos OMS'
} | ConvertTo-Json

$orgs = Invoke-RestMethod -Method Post `
    -Uri "https://app.harness.io/ng/api/org/filter?accountIdentifier=$account&pageIndex=0&pageSize=20" `
    -Headers $headers -Body $orgFilter -ContentType 'application/json'

Write-Host '--- Orgs matching Aptos OMS ---'
$orgs.data.content | Select-Object identifier, name | Format-Table -AutoSize

$orgId = $orgs.data.content[0].identifier
if (-not $orgId) { throw 'No org found' }

$projFilter = @{
    filterType = 'Project'
    searchTerm = 'OMS Development'
} | ConvertTo-Json

$projs = Invoke-RestMethod -Method Post `
    -Uri "https://app.harness.io/ng/api/projects/list?accountIdentifier=$account&orgIdentifier=$orgId&pageIndex=0&pageSize=20" `
    -Headers $headers -Body $projFilter -ContentType 'application/json'

Write-Host "--- Projects matching OMS Development (org $orgId) ---"
$projs.data.content | Select-Object identifier, name | Format-Table -AutoSize

Write-Host 'Suggested .env lines:'
Write-Host "HARNESS_ORG=$orgId"
if ($projs.data.content[0].identifier) {
    Write-Host "HARNESS_PROJECT=$($projs.data.content[0].identifier)"
}

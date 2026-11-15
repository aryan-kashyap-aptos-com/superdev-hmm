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
$h = @{ 'x-api-key' = $env:HARNESS_API_KEY; 'Harness-Account' = $account }
$exportDir = Join-Path $ConnectorRoot 'exports'
New-Item -ItemType Directory -Force -Path $exportDir | Out-Null
$out = Join-Path $exportDir 'scope-discovery.json'

$orgs = Invoke-RestMethod -Uri "https://app.harness.io/ng/api/aggregate/organizations?accountIdentifier=$account&pageIndex=0&pageSize=20" -Headers $h
$projs = Invoke-RestMethod -Uri "https://app.harness.io/ng/api/aggregate/projects?accountIdentifier=$account&pageIndex=0&pageSize=100" -Headers $h

$result = @{
    organizations = $orgs.data.content | ForEach-Object { @{ identifier = $_.organizationResponse.identifier; name = $_.organizationResponse.name } }
    omsProjects     = $projs.data.content | ForEach-Object {
        $p = $_.projectResponse
        if ($p.name -match 'OMS|Development|Sitemanager|sitemanager' -or $p.identifier -match 'OMS|sitemanager') {
            @{ org = $p.orgIdentifier; id = $p.identifier; name = $p.name }
        }
    }
}
$result | ConvertTo-Json -Depth 5 | Set-Content $out -Encoding UTF8
Get-Content $out

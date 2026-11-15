param([string] $Org = 'Aptos_OMS', [string] $Search = 'OMS')

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

$body = (@{ filterType = 'Project'; searchTerm = $Search } | ConvertTo-Json -Compress)
$uri = "https://app.harness.io/ng/api/projects/list?accountIdentifier=$account&orgIdentifier=$Org&pageIndex=0&pageSize=30"
try {
    $r = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $body -ContentType 'application/json'
    $r.data.content | Select-Object identifier, name | Format-Table -AutoSize
} catch {
    Write-Host $_.ErrorDetails.Message
}

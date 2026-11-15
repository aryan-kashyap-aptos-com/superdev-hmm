# Try likely org identifiers with known project id from Harness UI (OMS_Development).
$ErrorActionPreference = 'Continue'
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
$project = 'OMS_Development'
$orgCandidates = @(
    'Aptos_OMS', 'AptosOMS', 'aptos_oms', 'Aptos_O_M_S', 'AptosOMSOrg', 'default'
)

foreach ($org in $orgCandidates) {
    $uri = "https://app.harness.io/pipeline/api/pipelines/list?accountIdentifier=$account&orgIdentifier=$org&projectIdentifier=$project&pageIndex=0&pageSize=5"
    try {
        $body = '{"filterType":"PipelineSetup"}'
        $r = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $body -ContentType 'application/json'
        $count = @($r.data.content).Count
        if ($count -ge 0 -and $r.status -ne 'ERROR') {
            Write-Host "OK org=$org project=$project pipeline_count=$count"
            if ($count -gt 0) {
                $r.data.content | Select-Object -First 3 identifier, name | Format-Table -AutoSize
            }
        }
    } catch {
        $resp = $_.ErrorDetails.Message
        if (-not $resp) { $resp = $_.Exception.Message }
        Write-Host "fail org=$org - $resp"
    }
}

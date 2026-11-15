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
$project = $env:HARNESS_PROJECT
$orgs = @('Aptos_OMS', 'AptosOMS', 'aptos_oms', 'Aptos_OMS_Org', 'default')

foreach ($org in $orgs) {
    $uris = @(
        "https://app.harness.io/pipeline/api/pipelines/execution/summary?accountIdentifier=$account&orgIdentifier=$org&projectIdentifier=$project&pageIndex=0&pageSize=3",
        "https://app.harness.io/pipeline/api/pipeline/executions/summary?accountIdentifier=$account&orgIdentifier=$org&projectIdentifier=$project&pageIndex=0&pageSize=3"
    )
    foreach ($uri in $uris) {
        try {
            $r = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body '{"filterType":"PipelineExecution"}' -ContentType 'application/json'
            Write-Host "OK org=$org path=$($uri.Split('?')[0].Split('/')[-1]) count=$(@($r.data.content).Count)"
            $r.data.content | Select-Object -First 2 status, pipelineIdentifier, planExecutionId | Format-Table
        } catch {
            $code = $_.ErrorDetails.Message
            if ($code.Length -gt 120) { $code = $code.Substring(0, 120) + '...' }
            Write-Host "fail org=$org $($uri.Split('/')[-2]) $code"
        }
    }
}

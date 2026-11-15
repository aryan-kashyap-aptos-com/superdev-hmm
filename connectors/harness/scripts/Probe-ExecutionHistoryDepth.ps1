$ErrorActionPreference = 'Stop'
$ConnectorRoot = Split-Path -Parent $PSScriptRoot
Get-Content (Join-Path $ConnectorRoot '.env') | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq '' -or $line.StartsWith('#')) { return }
    $eq = $line.IndexOf('=')
    if ($eq -lt 1) { return }
    Set-Item -Path "Env:$($line.Substring(0, $eq).Trim())" -Value $line.Substring($eq + 1).Trim()
}
$m = [regex]::Match($env:HARNESS_API_KEY, '^pat\.([^.]+)\.')
$account = $m.Groups[1].Value
$org = $env:HARNESS_ORG
$h = @{ 'x-api-key' = $env:HARNESS_API_KEY; 'Harness-Account' = $account; 'Content-Type' = 'application/json' }

$projects = @('OMS_Development', 'OMS_DevOps')
foreach ($proj in $projects) {
    Write-Host "`n--- $org / $proj ---"
    foreach ($path in @('pipelines', 'pipeline')) {
        $uri = "https://app.harness.io/pipeline/api/$path/execution/summary?accountIdentifier=$account&orgIdentifier=$org&projectIdentifier=$proj&pageIndex=0&pageSize=5"
        try {
            $r = Invoke-RestMethod -Method Post -Uri $uri -Headers $h -Body '{"filterType":"PipelineExecution"}'
            $pipelines = $r.data.content | Group-Object pipelineIdentifier | ForEach-Object { "$($_.Name)=$($_.Count)" }
            Write-Host "  $path OK total=$($r.data.total) sample: $($pipelines -join ', ')"
        } catch {
            Write-Host "  $path fail: $($_.Exception.Message)"
        }
    }
}

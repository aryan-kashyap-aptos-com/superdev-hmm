param(
    [string] $Org = $env:HARNESS_ORG,
    [string] $Project = $env:HARNESS_PROJECT,
    [string] $Status = '',  # Failed, Success, Running, etc.
    [int] $Size = 15
)

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
if (-not $Org) { $Org = $env:HARNESS_ORG }
if (-not $Project) { $Project = $env:HARNESS_PROJECT }

$m = [regex]::Match($env:HARNESS_API_KEY, '^pat\.([^.]+)\.')
$account = $m.Groups[1].Value
$headers = @{ 'x-api-key' = $env:HARNESS_API_KEY }

$bodyObj = @{ filterType = 'PipelineExecution' }
if ($Status) { $bodyObj['pipelineExecutionStatuses'] = @($Status) }
$body = $bodyObj | ConvertTo-Json -Compress

$uri = "https://app.harness.io/pipeline/api/pipeline/executions/summary?accountIdentifier=$account&orgIdentifier=$Org&projectIdentifier=$Project&pageIndex=0&pageSize=$Size"
$r = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $body -ContentType 'application/json'

$r.data.content | ForEach-Object {
    [PSCustomObject]@{
        status      = $_.status
        pipeline    = $_.pipelineIdentifier
        name        = $_.name
        planExecId  = $_.planExecutionId
        started     = $_.startTs
        branch      = $_.moduleInfo.branch
    }
} | Format-Table -AutoSize

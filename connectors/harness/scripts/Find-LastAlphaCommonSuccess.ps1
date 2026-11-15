# Last oms_release_pipeline successes: overall green vs alpha_common (Linux React) vs alpha_windows.
param([int] $MaxPages = 80, [int] $PageSize = 100)

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
$proj = $env:HARNESS_PROJECT
$h = @{ 'x-api-key' = $env:HARNESS_API_KEY; 'Harness-Account' = $account; 'Content-Type' = 'application/json' }

function Get-StageMeta([string] $execId) {
    $q = "accountIdentifier=$account&orgIdentifier=$org&projectIdentifier=$proj"
    $detail = Invoke-RestMethod -Method Get -Uri "https://app.harness.io/pipeline/api/pipelines/execution/${execId}?$q" -Headers $h
    $nodes = @()
    if ($detail.data.executionGraph.nodeMap) {
        $nodes = $detail.data.executionGraph.nodeMap.PSObject.Properties.Value
    }
    $ac = $nodes | Where-Object { $_.name -eq 'alpha_common' } | Select-Object -First 1
    $aw = $nodes | Where-Object { $_.name -eq 'alpha_windows' } | Select-Object -First 1
    $s = $detail.data.pipelineExecutionSummary
    $tag = $s.moduleInfo.ci.codebaseTag
    if (-not $tag -and $s.executionTriggerInfo.triggeredBy.extraInfo.sourceEventId) {
        $tag = $s.executionTriggerInfo.triggeredBy.extraInfo.sourceEventId
    }
    return @{
        alpha_common  = $(if ($ac) { $ac.status } else { 'missing' })
        alpha_windows = $(if ($aw) { $aw.status } else { 'n/a' })
        tag           = $tag
        trigger       = $s.executionTriggerInfo.triggeredBy.identifier
    }
}

function New-Row($ex, $meta) {
    [PSCustomObject]@{
        started       = [DateTimeOffset]::FromUnixTimeMilliseconds([int64]$ex.startTs).ToString('yyyy-MM-dd HH:mm:ss UTC')
        execId        = $ex.planExecutionId
        pipelineStatus = $ex.status
        alpha_common  = $meta.alpha_common
        alpha_windows = $meta.alpha_windows
        tag           = $meta.tag
        trigger       = $meta.trigger
    }
}

$lastPipelineSuccess = $null
$lastAlphaCommonSuccess = $null
$lastAlphaWindowsSuccess = $null
$seen = @{}
$omsCount = 0
$apiTotal = $null

for ($page = 0; $page -lt $MaxPages; $page++) {
    $uri = "https://app.harness.io/pipeline/api/pipelines/execution/summary?accountIdentifier=$account&orgIdentifier=$org&projectIdentifier=$proj&pageIndex=$page&pageSize=$PageSize"
    $body = '{"filterType":"PipelineExecution","pipelineIdentifier":"oms_release_pipeline"}'
    try {
        $summary = Invoke-RestMethod -Method Post -Uri $uri -Headers $h -Body $body
    } catch {
        if ($page -eq 0) {
            $body = '{"filterType":"PipelineExecution"}'
            $summary = Invoke-RestMethod -Method Post -Uri $uri -Headers $h -Body $body
        } else { throw }
    }
    if ($null -eq $apiTotal -and $summary.data.total) { $apiTotal = $summary.data.total }
    if (-not $summary.data.content -or $summary.data.content.Count -eq 0) { break }

    foreach ($ex in ($summary.data.content | Sort-Object { [int64]$_.startTs } -Descending)) {
        if ($ex.pipelineIdentifier -ne 'oms_release_pipeline') { continue }
        if ($seen.ContainsKey($ex.planExecutionId)) { continue }
        $seen[$ex.planExecutionId] = $true
        $omsCount++

        $meta = Get-StageMeta $ex.planExecutionId
        $row = New-Row $ex $meta

        if ($ex.status -eq 'Success' -and -not $lastPipelineSuccess) { $lastPipelineSuccess = $row }
        if ($meta.alpha_common -eq 'Success' -and -not $lastAlphaCommonSuccess) { $lastAlphaCommonSuccess = $row }
        if ($meta.alpha_windows -eq 'Success' -and -not $lastAlphaWindowsSuccess) { $lastAlphaWindowsSuccess = $row }

        if ($lastPipelineSuccess -and $lastAlphaCommonSuccess) { break }
    }
    if ($lastPipelineSuccess -and $lastAlphaCommonSuccess) { break }
    if ($summary.data.content.Count -lt $PageSize) { break }
}

Write-Host "API reported total (if any): $apiTotal"
Write-Host "Unique oms_release_pipeline executions scanned: $omsCount`n"

Write-Host '=== Last overall pipeline Success (oms_release_pipeline) ==='
if ($lastPipelineSuccess) { $lastPipelineSuccess | Format-List } else { Write-Host 'None found in scan.' }

Write-Host '=== Last alpha_common Success (Linux React / npgsql stage) ==='
if ($lastAlphaCommonSuccess) { $lastAlphaCommonSuccess | Format-List } else { Write-Host 'None found in scan.' }

Write-Host '=== Last alpha_windows Success (Windows alpha stage) ==='
if ($lastAlphaWindowsSuccess) { $lastAlphaWindowsSuccess | Format-List } else { Write-Host 'None found in scan.' }

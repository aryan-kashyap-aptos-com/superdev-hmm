# Last N days: which oms_release_pipeline runs had alpha_common (React/npgsql Linux CI) execute.
param([int] $Days = 3, [int] $PageSize = 40)

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
$cutoff = [DateTimeOffset]::UtcNow.AddDays(-$Days).ToUnixTimeMilliseconds()

$allExecs = @()
for ($page = 0; $page -lt 8; $page++) {
    $uri = "https://app.harness.io/pipeline/api/pipelines/execution/summary?accountIdentifier=$account&orgIdentifier=$org&projectIdentifier=$proj&pageIndex=$page&pageSize=$PageSize"
    $summary = Invoke-RestMethod -Method Post -Uri $uri -Headers $h -Body '{"filterType":"PipelineExecution"}'
    if (-not $summary.data.content -or $summary.data.content.Count -eq 0) { break }
    $allExecs += $summary.data.content
    $oldest = ($summary.data.content | Sort-Object startTs | Select-Object -First 1).startTs
    if ($oldest -lt $cutoff) { break }
}

$seen = @{}
$allExecs = $allExecs | Where-Object {
    if ($seen.ContainsKey($_.planExecutionId)) { return $false }
    $seen[$_.planExecutionId] = $true
    return $true
}

$rows = @()
foreach ($ex in $allExecs) {
    if ($ex.startTs -lt $cutoff) { continue }
    if ($ex.pipelineIdentifier -ne 'oms_release_pipeline') { continue }

    $q = "accountIdentifier=$account&orgIdentifier=$org&projectIdentifier=$proj"
    $detailUri = "https://app.harness.io/pipeline/api/pipelines/execution/$($ex.planExecutionId)?$q"
    $detail = Invoke-RestMethod -Method Get -Uri $detailUri -Headers $h
    $nodes = @()
    if ($detail.data.executionGraph.nodeMap) {
        $nodes = $detail.data.executionGraph.nodeMap.PSObject.Properties.Value
    }
    $alphaCommon = $nodes | Where-Object { $_.nodeIdentifier -eq 'alpha' -or $_.identifier -eq 'alpha' -or $_.name -match 'alpha_common' } | Select-Object -First 1
    $alphaWin = $nodes | Where-Object { $_.nodeIdentifier -eq 'alpha_win' -or $_.identifier -eq 'alpha_win' } | Select-Object -First 1

    $alphaCommonStatus = 'n/a'
    foreach ($n in $nodes) {
        if ($n.name -eq 'alpha_common' -or $n.nodeIdentifier -eq 'alpha') {
            if ($n.name -eq 'alpha_common') { $alphaCommonStatus = $n.status; break }
        }
    }
    if ($alphaCommonStatus -eq 'n/a') {
        $ac = $nodes | Where-Object { $_.name -eq 'alpha_common' } | Select-Object -First 1
        if ($ac) { $alphaCommonStatus = $ac.status }
    }

    $tag = $ex.moduleInfo.ci.codebaseTag
    if (-not $tag) { $tag = $detail.data.pipelineExecutionSummary.executionTriggerInfo.triggeredBy.extraInfo.sourceEventId }

    $started = [DateTimeOffset]::FromUnixTimeMilliseconds([int64]$ex.startTs).ToString('yyyy-MM-dd HH:mm UTC')

    $reactLikely = ($alphaCommonStatus -eq 'Success')
    $rows += [PSCustomObject]@{
        started            = $started
        pipeline           = $ex.pipelineIdentifier
        status             = $ex.status
        execId             = $ex.planExecutionId
        alpha_common       = $alphaCommonStatus
        alpha_windows      = $(if ($alphaWin) { $alphaWin.status } else { 'n/a' })
        react_in_build     = $(if ($reactLikely) { 'YES' } else { 'NO' })
    }
}

Write-Host "Cutoff: last $Days days (since $([DateTimeOffset]::FromUnixTimeMilliseconds($cutoff).ToString('yyyy-MM-dd HH:mm UTC')))`n"
$rows | Sort-Object started -Descending | Format-Table -AutoSize

$yes = @($rows | Where-Object { $_.react_in_build -eq 'YES' })
Write-Host "Runs with alpha_common Success (React/npgsql Linux stage ran): $($yes.Count)"
if ($yes.Count -gt 0) {
    $yes | Select-Object started, execId, status, pipeline | Format-Table -AutoSize
}

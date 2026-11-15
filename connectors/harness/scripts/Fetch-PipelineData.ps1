# Discover scope, list recent executions, pull failed-step log excerpts.
param(
    [int] $ExecutionLimit = 8,
    [string] $OutDir = ''
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

$m = [regex]::Match($env:HARNESS_API_KEY, '^pat\.([^.]+)\.')
$account = $m.Groups[1].Value
$headers = @{
    'x-api-key'           = $env:HARNESS_API_KEY
    'Harness-Account'     = $account
    'Content-Type'        = 'application/json'
}

function Invoke-Harness([string] $Method, [string] $Uri, [string] $Body = $null) {
    if ($Body) {
        return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers -Body $Body
    }
    return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers
}

# Find OMS Development project (org + project ids)
$scopeOrg = $env:HARNESS_ORG
$scopeProject = $env:HARNESS_PROJECT
$found = $false

$orgList = Invoke-Harness GET "https://app.harness.io/ng/api/aggregate/organizations?accountIdentifier=$account&pageIndex=0&pageSize=100"
$orgs = @($orgList.data.content | ForEach-Object { $_.organizationResponse.organization } | Where-Object { $_.identifier })
if ($orgs.Count -eq 0) {
    $orgs = @([PSCustomObject]@{ identifier = $scopeOrg })
}

foreach ($o in $orgs) {
    $oid = $o.identifier
    if (-not $oid) { continue }
    $filter = '{"filterType":"Project","searchTerm":"OMS Development"}'
    $uri = "https://app.harness.io/ng/api/projects/list?accountIdentifier=$account&orgIdentifier=$oid&pageIndex=0&pageSize=30"
    try {
        $pr = Invoke-Harness POST $uri $filter
        $match = $pr.data.content | Where-Object { $_.identifier -eq 'OMS_Development' -or $_.name -match 'OMS Development' } | Select-Object -First 1
        if ($match) {
            $scopeOrg = $oid
            $scopeProject = $match.identifier
            $found = $true
            Write-Host "Scope: org=$scopeOrg project=$scopeProject ($($match.name))"
            break
        }
    } catch {
        continue
    }
}

if (-not $found) {
    Write-Host "Using .env scope: org=$scopeOrg project=$scopeProject"
}

$summaryUri = "https://app.harness.io/pipeline/api/pipelines/execution/summary?accountIdentifier=$account&orgIdentifier=$scopeOrg&projectIdentifier=$scopeProject&pageIndex=0&pageSize=$ExecutionLimit"
$summaryBody = '{"filterType":"PipelineExecution"}'
$summary = Invoke-Harness POST $summaryUri $summaryBody

Write-Host "`n--- Recent executions ---"
$summary.data.content | ForEach-Object {
    [PSCustomObject]@{
        status   = $_.status
        pipeline = $_.pipelineIdentifier
        execId   = $_.planExecutionId
        branch   = $_.moduleInfo.branch
        started  = $_.startTs
    }
} | Format-Table -AutoSize

$target = $summary.data.content | Where-Object { $_.status -in @('Failed', 'Aborted', 'Expired') -and $_.pipelineIdentifier -eq 'oms_release_pipeline' } | Select-Object -First 1
if (-not $target) {
    $target = $summary.data.content | Where-Object { $_.status -in @('Failed', 'Aborted', 'Expired') } | Select-Object -First 1
}
if (-not $target) {
    $target = $summary.data.content | Select-Object -First 1
}

if (-not $target) {
    Write-Host 'No executions returned.'
    exit 0
}

$execId = $target.planExecutionId
Write-Host "`n--- Execution detail: $execId ($($target.pipelineIdentifier)) status=$($target.status) ---"

$q = "accountIdentifier=$account&orgIdentifier=$scopeOrg&projectIdentifier=$scopeProject"
$detailUri = "https://app.harness.io/pipeline/api/pipelines/execution/${execId}?$q"
Write-Host "GET $detailUri"
try {
    $detail = Invoke-Harness GET $detailUri
} catch {
    $detailUri = "https://app.harness.io/pipeline/api/pipelines/execution/v2/${execId}?$q"
    Write-Host "Retry GET $detailUri"
    $detail = Invoke-Harness GET $detailUri
}

$failedNodes = [System.Collections.ArrayList]::new()
function Walk-Nodes($nodes) {
    foreach ($n in $nodes) {
        if ($n.status -eq 'Failed' -or $n.status -eq 'Errored') {
            [void]$failedNodes.Add($n)
        }
        if ($n.children) { Walk-Nodes $n.children }
    }
}
if ($detail.data.executionGraph) {
    Walk-Nodes $detail.data.executionGraph.nodeMap.PSObject.Properties.Value
}

if ($failedNodes.Count -eq 0 -and $detail.data.executionGraph.nodeMap) {
    $failedNodes = $detail.data.executionGraph.nodeMap.PSObject.Properties.Value | Where-Object { $_.name -match 'Build OMS|buildreact|npgsql|React|unittests' } | Select-Object -First 3
}

if ($OutDir) {
    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
    $detail | ConvertTo-Json -Depth 12 | Set-Content (Join-Path $OutDir 'execution-detail.json') -Encoding UTF8
}

foreach ($node in $failedNodes | Select-Object -First 3) {
    Write-Host "`n=== Step: $($node.name) status=$($node.status) ==="
    $logBase = "https://app.harness.io/log-service/v1/logs?accountID=$account&orgId=$scopeOrg&projectId=$scopeProject"
    $params = "pipelineExecutionId=$execId&stageNodeId=$($node.uuid)&stepType=$([uri]::EscapeDataString($node.stepType))"
    try {
        $logUri = "$logBase&$params"
        $logs = Invoke-Harness GET $logUri
        $lines = @()
        foreach ($blob in $logs.data) {
            if ($blob.logData) { $lines += $blob.logData }
        }
        $text = ($lines | Select-Object -Last 80) -join "`n"
        if ($text.Length -gt 12000) { $text = $text.Substring($text.Length - 12000) }
        Write-Host $text
        if ($OutDir) {
            $safe = ($node.name -replace '[^\w\-]', '_')
            Set-Content (Join-Path $OutDir "log-$safe.txt") -Value $text -Encoding UTF8
        }
    } catch {
        Write-Host "Log fetch failed: $($_.ErrorDetails.Message)"
    }
}

Write-Host "`nDone. execId=$execId org=$scopeOrg project=$scopeProject"

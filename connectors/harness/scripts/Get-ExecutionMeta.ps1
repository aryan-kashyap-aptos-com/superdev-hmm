param([string] $ExecId = 'kHsWghZhTf6SqXxa7hU3gg')
$ConnectorRoot = Split-Path -Parent $PSScriptRoot
Get-Content (Join-Path $ConnectorRoot '.env') | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.*)$') { Set-Item -Path "Env:$($matches[1].Trim())" -Value $matches[2].Trim() }
}
$account = '82alj-w-QGSN-OFFBTv9Ew'
$org = $env:HARNESS_ORG
$proj = $env:HARNESS_PROJECT
$h = @{ 'x-api-key' = $env:HARNESS_API_KEY; 'Harness-Account' = $account }
$q = "accountIdentifier=$account&orgIdentifier=$org&projectIdentifier=$proj"
$uri = "https://app.harness.io/pipeline/api/pipelines/execution/${ExecId}?$q"
$r = Invoke-RestMethod -Uri $uri -Headers $h
$s = $r.data.pipelineExecutionSummary
Write-Host "pipeline=$($s.pipelineIdentifier) status=$($s.status) name=$($s.name)"
Write-Host "trigger=$($s.executionTriggerInfo.triggerType) by=$($s.executionTriggerInfo.triggeredBy.identifier)"
if ($s.moduleInfo.ci) { $s.moduleInfo.ci | ConvertTo-Json -Depth 4 }
if ($s.executionTriggerInfo.triggeredBy.extraInfo) { $s.executionTriggerInfo.triggeredBy.extraInfo | ConvertTo-Json }
if ($r.data.executionGraph.nodeMap) {
    Write-Host "`n--- nodes ---"
    $r.data.executionGraph.nodeMap.PSObject.Properties.Value |
        Select-Object name, status, identifier |
        Sort-Object name |
        Format-Table -AutoSize
}

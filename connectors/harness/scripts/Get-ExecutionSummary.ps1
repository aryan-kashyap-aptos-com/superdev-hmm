param([string] $ExecId)
$ConnectorRoot = Split-Path -Parent $PSScriptRoot
Get-Content (Join-Path $ConnectorRoot '.env') | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.*)$') { Set-Item -Path "Env:$($matches[1].Trim())" -Value $matches[2].Trim() }
}
$account = ([regex]::Match($env:HARNESS_API_KEY, '^pat\.([^.]+)\.')).Groups[1].Value
$h = @{ 'x-api-key' = $env:HARNESS_API_KEY; 'Harness-Account' = $account }
$q = "accountIdentifier=$account&orgIdentifier=$($env:HARNESS_ORG)&projectIdentifier=$($env:HARNESS_PROJECT)"
$r = Invoke-RestMethod -Uri "https://app.harness.io/pipeline/api/pipelines/execution/$ExecId?$q" -Headers $h
$s = $r.data.pipelineExecutionSummary
Write-Host "status=$($s.status) inputSets=$($s.inputSetIdentifiers -join ',')"
Write-Host "branch=$($s.moduleInfo.branch) tag=$($s.moduleInfo.ci.codebaseTag)"
if ($s.pipelineVariables) { $s.pipelineVariables | ConvertTo-Json -Depth 5 }
$r.data.executionGraph.nodeMap.PSObject.Properties.Value | Select-Object name, status | Sort-Object name | Format-Table -AutoSize

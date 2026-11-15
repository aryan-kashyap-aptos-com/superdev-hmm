# Read-only: fetch oms_push input set + pipeline runtime template for learning/docs.
param(
    [string] $PipelineId = 'oms_release_pipeline',
    [string] $InputSetId = 'oms_push'
)

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
$h = @{ 'x-api-key' = $env:HARNESS_API_KEY; 'Harness-Account' = $account }

$outDir = Join-Path $ConnectorRoot 'exports'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$endpoints = @(
    @{
        Name = 'inputSet-detail'
        Uri  = "https://app.harness.io/pipeline/api/inputSets/$InputSetId?accountIdentifier=$account&orgIdentifier=$org&projectIdentifier=$proj"
        Method = 'Get'
    },
    @{
        Name = 'inputSet-template'
        Uri  = "https://app.harness.io/pipeline/api/inputSets/template?accountIdentifier=$account&orgIdentifier=$org&projectIdentifier=$proj&pipelineIdentifier=$PipelineId&inputSetIdentifier=$InputSetId"
        Method = 'Get'
    },
    @{
        Name = 'pipeline-inputs-template'
        Uri  = "https://app.harness.io/pipeline/api/pipelines/templateInputs/$PipelineId?accountIdentifier=$account&orgIdentifier=$org&projectIdentifier=$proj"
        Method = 'Get'
    }
)

foreach ($ep in $endpoints) {
    $path = Join-Path $outDir ("oms-push-{0}.json" -f $ep.Name)
    try {
        $r = Invoke-RestMethod -Method $ep.Method -Uri $ep.Uri -Headers $h
        $r | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $path -Encoding utf8
        Write-Host "OK $($ep.Name) -> $path"
    } catch {
        Write-Host "FAIL $($ep.Name): $($_.Exception.Message)"
    }
}

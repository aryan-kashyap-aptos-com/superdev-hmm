# Smoke test: list orgs (no secrets printed). Optional: .\Test-HarnessApi.ps1 -SearchPipeline OMS
param([string] $SearchPipeline = '')

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

if (-not $env:HARNESS_API_KEY) { throw 'HARNESS_API_KEY missing' }

$m = [regex]::Match($env:HARNESS_API_KEY, '^pat\.([^.]+)\.')
if (-not $m.Success) { throw 'Could not parse account id from PAT' }
$account = $m.Groups[1].Value
$headers = @{ 'x-api-key' = $env:HARNESS_API_KEY }

$me = Invoke-RestMethod -Uri 'https://app.harness.io/ng/api/user/currentUser' -Headers $headers
Write-Host ('API key OK - user: ' + $me.data.user.email)

if ($me.data.accounts -and $me.data.accounts.Count -gt 0) {
    $me.data.accounts | Select-Object -First 3 name, uuid, identifier | Format-List
    $acct0 = $me.data.accounts[0]
    if ($acct0.identifier) { $account = $acct0.identifier }
    elseif ($acct0.uuid) { $account = $acct0.uuid }
    Write-Host ('Using account: ' + $account)
}

$orgs = Invoke-RestMethod -Uri "https://app.harness.io/ng/api/accounts/$account/orgs?limit=50" -Headers $headers
Write-Host "--- Organizations (account $account) ---"
$orgs.data.content | Select-Object identifier, name | Format-Table -AutoSize

if ($SearchPipeline) {
    foreach ($org in $orgs.data.content) {
        $oid = $org.identifier
        $projs = Invoke-RestMethod -Uri "https://app.harness.io/ng/api/accounts/$account/orgs/$oid/projects?limit=50" -Headers $headers
        foreach ($proj in $projs.data.content) {
            $pid = $proj.identifier
            $pipes = Invoke-RestMethod -Uri "https://app.harness.io/ng/api/accounts/$account/orgs/$oid/projects/$pid/pipelines/list?searchTerm=$SearchPipeline&size=10" -Headers $headers -Method Post -Body '{}' -ContentType 'application/json'
            foreach ($p in $pipes.data.content) {
                Write-Host ("PIPE: org={0} project={1} id={2} name={3}" -f $oid, $pid, $p.identifier, $p.name)
            }
        }
    }
}

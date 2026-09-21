# Print org/project identifiers for .env (no secrets).
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
$headers = @{ 'x-api-key' = $env:HARNESS_API_KEY }

$uris = @(
    "https://app.harness.io/ng/api/aggregate/organizations?accountIdentifier=$account&pageIndex=0&pageSize=50",
    "https://app.harness.io/ng/api/organizations?accountIdentifier=$account&pageIndex=0&pageSize=50"
)
foreach ($uri in $uris) {
    try {
        $r = Invoke-RestMethod -Uri $uri -Headers $headers -Method Get
        Write-Host "--- $uri ---"
        $items = @()
        if ($r.data.content) { $items = $r.data.content }
        elseif ($r.data.organizations) { $items = $r.data.organizations }
        elseif ($r.data -is [Array]) { $items = $r.data }
        $items | Select-Object identifier, name | Format-Table -AutoSize
    } catch {
        Write-Host "skip: $($uri.Split('/')[-1]) $($_.ErrorDetails.Message.Substring(0, [Math]::Min(80, $_.ErrorDetails.Message.Length)))"
    }
}

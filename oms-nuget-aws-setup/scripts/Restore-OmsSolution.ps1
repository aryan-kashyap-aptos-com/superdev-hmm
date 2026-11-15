# NuGet restore for DCEOM.All.sln into c:\oms\packages (run Login-CodeArtifact.ps1 first).
. "$PSScriptRoot\_Common.ps1"

$root = Get-OmsNuGetSetupRoot
$config = Get-OmsNuGetConfig
$envFile = Join-Path $root 'NugetAWS.env'

Import-NugetAwsEnv -EnvFile $envFile
$nuget = Get-NuGetExe -SetupRoot $root

$oms = $config.omsRepoPath
$solution = Join-Path $oms $config.solutionFile
if (-not (Test-Path $solution)) {
    throw "Solution not found: $solution"
}

Push-Location $oms
try {
    Write-Host "Restoring $solution ..."
    & $nuget restore $solution -PackagesDirectory $config.packagesDirectory -NonInteractive
    if ($LASTEXITCODE -ne 0) { throw "nuget restore failed with exit $LASTEXITCODE" }
    Write-Host 'Restore completed.'
}
finally {
    Pop-Location
}

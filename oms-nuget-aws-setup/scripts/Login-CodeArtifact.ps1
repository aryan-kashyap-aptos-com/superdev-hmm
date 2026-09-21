# Authenticates NuGet against AWS CodeArtifact (login lasts ~12 hours).
. "$PSScriptRoot\_Common.ps1"

$root = Get-OmsNuGetSetupRoot
$config = Get-OmsNuGetConfig
$envFile = Join-Path $root 'NugetAWS.env'

Import-NugetAwsEnv -EnvFile $envFile
$nuget = Get-NuGetExe -SetupRoot $root
$env:PATH = "$(Split-Path $nuget -Parent);$env:PATH"

Write-Host 'Checking AWS identity...'
aws sts get-caller-identity | Out-Host

Write-Host 'Logging NuGet into CodeArtifact...'
aws codeartifact login `
    --tool nuget `
    --domain $config.codeArtifact.domain `
    --domain-owner $config.codeArtifact.domainOwner `
    --repository $config.codeArtifact.repository `
    --region $config.codeArtifact.region

Write-Host 'Done. NuGet sources updated in your user NuGet.Config.'

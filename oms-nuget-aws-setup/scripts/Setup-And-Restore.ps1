# One-shot: CodeArtifact login + full solution package restore.
& "$PSScriptRoot\Login-CodeArtifact.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& "$PSScriptRoot\Restore-OmsSolution.ps1"
exit $LASTEXITCODE

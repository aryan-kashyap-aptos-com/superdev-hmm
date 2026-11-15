param(
    [ValidateSet('Debug', 'Release')]
    [string] $Configuration = 'Debug'
)

# Builds ODX monitor + Shipping slice (same projects validated locally for DCOMS-29203).
. "$PSScriptRoot\_Common.ps1"

$config = Get-OmsNuGetConfig
$msbuild = Get-MsBuildExe
$oms = $config.omsRepoPath

Push-Location $oms
try {
    foreach ($rel in $config.odxBuildProjects) {
        $proj = Join-Path $oms $rel
        if (-not (Test-Path $proj)) {
            throw "Project not found: $proj"
        }
        Write-Host "`n======== BUILD $rel ========"
        & $msbuild $proj /t:Build /p:Configuration=$Configuration /v:minimal /nologo
        if ($LASTEXITCODE -ne 0) {
            throw "Build failed: $rel (exit $LASTEXITCODE)"
        }
    }
    Write-Host "`nAll ODX slice projects built successfully ($Configuration)."
}
finally {
    Pop-Location
}

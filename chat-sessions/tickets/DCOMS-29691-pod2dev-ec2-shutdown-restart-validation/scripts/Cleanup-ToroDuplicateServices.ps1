# Keep only the latest toronado service set (highest deploy sequence suffix).
param(
    [string] $KeepSuffix = '50092'
)

$ErrorActionPreference = 'Stop'
$keep = @(
    "OMS-JobManager-pod2dev-$KeepSuffix",
    "OMS-JobProcessor-pod2dev-$KeepSuffix",
    "OMS-PostOffice-pod2dev-$KeepSuffix"
)

Write-Host "Keeping: $($keep -join ', ')"
Write-Host ""

$all = Get-Service OMS-* -ErrorAction SilentlyContinue
if (-not $all) {
    Write-Host 'No OMS-* services found.'
    exit 0
}

foreach ($svc in $all | Sort-Object Name) {
    if ($keep -contains $svc.Name) {
        if ($svc.Status -ne 'Running') {
            Write-Host "[START] $($svc.Name)"
            Start-Service $svc.Name
        } else {
            Write-Host "[KEEP ] $($svc.Name) ($($svc.Status))"
        }
        continue
    }

    Write-Host "[REMOVE] $($svc.Name) ($($svc.Status))"
    if ($svc.Status -eq 'Running') {
        Stop-Service $svc.Name -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
    }

    $wmi = Get-CimInstance Win32_Service -Filter "Name='$($svc.Name)'" -ErrorAction SilentlyContinue
    $bin = $wmi.PathName
    sc.exe delete $svc.Name | Out-Host
    Start-Sleep -Seconds 3

    if ($bin) {
        $exe = $bin.Trim('"').Split(' ')[0]
        $dir = Split-Path $exe -Parent
        if ($dir -and (Test-Path $dir)) {
            Write-Host "  removing folder $dir"
            Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host ""
Write-Host 'Remaining services:'
Get-Service OMS-* | Format-Table Name, Status, StartType -AutoSize

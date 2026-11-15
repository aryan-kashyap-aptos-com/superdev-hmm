#Requires -Version 5.1
<#
.SYNOPSIS
  Pod2-dev Site Manager health check (IIS, content paths, ALB targets).

.DESCRIPTION
  Run on the Site Manager EC2 (RDP) or any Windows host with IIS + optional AWS CLI.
  Checks the items needed after terminate/redeploy: pod2-dev-sm site, hashcheck.asp, backadmin.

.EXAMPLE
  .\Check-Pod2Dev-SM-Health.ps1

.EXAMPLE
  .\Check-Pod2Dev-SM-Health.ps1 -Space pod2 -Environment dev -AwsRegion us-east-1
#>
[CmdletBinding()]
param(
    [string] $Space = 'pod2',
    [string] $Environment = 'dev',
    [string] $Product = 'oms',
    [string] $AwsRegion = 'us-east-1',
    [string] $UncSmPath = '\\omspod.aptos.com\pod2-dev\dev\sm',
    [string] $LocalContentPath = 'D:\content\pod2\sm',
    [switch] $SkipAws
)

$ErrorActionPreference = 'Continue'
$smSite = "$Space-$Environment-sm"
$izendaSite = "$Space-$Environment-izenda"

function Write-Section([string]$Title) {
    Write-Host ""
    Write-Host ("=" * 72) -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host ("=" * 72) -ForegroundColor Cyan
}

function Write-Result([string]$Label, [bool]$Ok, [string]$Detail = '') {
    $status = if ($Ok) { 'PASS' } else { 'FAIL' }
    $color  = if ($Ok) { 'Green' } else { 'Red' }
    $line   = if ($Detail) { "[$status] $Label - $Detail" } else { "[$status] $Label" }
    Write-Host $line -ForegroundColor $color
}

$failures = [System.Collections.Generic.List[string]]::new()

function Record-Fail([string]$Message) {
    if (-not $failures.Contains($Message)) { [void]$failures.Add($Message) }
}

Write-Section "Host"
Write-Host "Computer : $env:COMPUTERNAME"
Write-Host "User     : $env:USERNAME"
Write-Host "Time     : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K')"

# --- IIS module ---
Write-Section "IIS"
$iisOk = $false
try {
    Import-Module WebAdministration -ErrorAction Stop
    $iisOk = $true
    Write-Result 'WebAdministration module' $true
}
catch {
    Write-Result 'WebAdministration module' $false $_.Exception.Message
    Record-Fail 'IIS WebAdministration module not available (run on SM server with IIS).'
}

if ($iisOk) {
    $sites = @(Get-Website | Sort-Object Name)
    Write-Host ""
    Write-Host "Sites ($($sites.Count)):"
    foreach ($s in $sites) {
        $path = (Get-ItemProperty "IIS:\Sites\$($s.Name)" -ErrorAction SilentlyContinue).physicalPath
        $pool = (Get-ItemProperty "IIS:\Sites\$($s.Name)" -ErrorAction SilentlyContinue).applicationPool
        Write-Host ("  {0,-30} {1,-8} pool={2}" -f $s.Name, $s.State, $pool)
        Write-Host ("    path: {0}" -f $path)
        foreach ($b in $s.bindings.Collection) {
            Write-Host ("    binding: {0}://{1}" -f $b.protocol, $b.bindingInformation)
        }
    }

    $sm = $sites | Where-Object { $_.Name -eq $smSite }
    $iz = $sites | Where-Object { $_.Name -eq $izendaSite }
    Write-Result "IIS site '$smSite' exists" ([bool]$sm)
    Write-Result "IIS site '$izendaSite' exists" ([bool]$iz)
    if (-not $sm) { Record-Fail "Missing IIS site '$smSite' (sitemanager_server_setup may not have run)." }

    if ($sm) {
        $smPath = (Get-ItemProperty "IIS:\Sites\$smSite").physicalPath
        Write-Host "SM physical path: $smPath"
    }
}

# --- File / UNC checks ---
Write-Section "Content paths"
$pathsToCheck = [ordered]@{
    'UNC SM root'              = $UncSmPath
    'UNC hashcheck.asp'        = Join-Path $UncSmPath 'hashcheck.asp'
    'UNC backadmin login'      = Join-Path $UncSmPath 'backadmin\login.aspx'
    'Local content SM root'    = $LocalContentPath
    'Local hashcheck.asp'      = Join-Path $LocalContentPath 'hashcheck.asp'
    'Local backadmin login'    = Join-Path $LocalContentPath 'backadmin\login.aspx'
}

foreach ($entry in $pathsToCheck.GetEnumerator()) {
    $exists = Test-Path -LiteralPath $entry.Value -ErrorAction SilentlyContinue
    Write-Result $entry.Key $exists $entry.Value
    if (-not $exists) {
        if ($entry.Key -like 'UNC*') {
            Record-Fail "$($entry.Key) missing: $($entry.Value)"
        }
        if ($entry.Key -like 'Local*') {
            Record-Fail "$($entry.Key) missing: $($entry.Value) (sitemanager_deploy / content server)."
        }
    }
}

# --- HTTP probe (localhost + SM host header if known) ---
Write-Section "HTTP probes"
$hashOk = $false
$loginOk = $false

if ($iisOk -and $sm) {
    $smBindings = (Get-Website -Name $smSite).bindings.Collection |
        Where-Object { $_.protocol -eq 'http' }
    $hostHeader = 'localhost'
    foreach ($b in $smBindings) {
        # bindingInformation format: *:80:hostname
        $parts = $b.bindingInformation -split ':'
        if ($parts.Count -ge 3 -and $parts[2]) { $hostHeader = $parts[2]; break }
    }
    Write-Host "Using host header: $hostHeader"

    try {
        $hashResp = Invoke-WebRequest -Uri "http://203.0.113.22/hashcheck.asp" -Headers @{ Host = $hostHeader } `
            -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
        $hashOk = ($hashResp.StatusCode -eq 200)
        Write-Result '/hashcheck.asp (ALB health path)' $hashOk "HTTP $($hashResp.StatusCode)"
    }
    catch {
        Write-Result '/hashcheck.asp (ALB health path)' $false $_.Exception.Message
        Record-Fail "hashcheck.asp not reachable on SM site (ALB will stay unhealthy)."
    }

    try {
        $loginResp = Invoke-WebRequest -Uri "http://203.0.113.22/backadmin/login.aspx" -Headers @{ Host = $hostHeader } `
            -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
        $loginOk = ($loginResp.StatusCode -eq 200)
        Write-Result '/backadmin/login.aspx' $loginOk "HTTP $($loginResp.StatusCode)"
    }
    catch {
        $code = $null
        if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
        $detail = if ($code) { "HTTP $code - $($_.Exception.Message)" } else { $_.Exception.Message }
        Write-Result '/backadmin/login.aspx' $false $detail
        if ($code -eq 500) {
            Record-Fail 'login.aspx returns 500 - app/config/DB issue (IIS site may exist but app broken).'
        }
        else {
            Record-Fail "login.aspx not reachable: $detail"
        }
    }
}
else {
    Write-Host 'Skipping HTTP probes (no SM IIS site).'
}

# --- AWS: SSM endpoints + ALB target health ---
if (-not $SkipAws) {
    Write-Section "AWS (SSM + ALB)"
    $awsCli = Get-Command aws -ErrorAction SilentlyContinue
    if (-not $awsCli) {
        Write-Host 'AWS CLI not found - skipping SSM/ALB checks. Use -SkipAws to hide this section.' -ForegroundColor Yellow
    }
    else {
        $ssmParams = @(
            "/$Product/$Space/$Environment/sm/endpoint",
            "/$Product/$Space/$Environment/api/endpoint",
            "/$Product/$Space/$Environment/services/endpoint",
            "/$Product/$Space/$Environment/sm/dbconnstr/host"
        )
        foreach ($p in $ssmParams) {
            try {
                $val = aws ssm get-parameter --name $p --region $AwsRegion --query 'Parameter.Value' --output text 2>$null
                $ok = ($LASTEXITCODE -eq 0) -and $val -and $val -ne 'None'
                Write-Result $p $ok $(if ($ok) { $val } else { 'not found or no access' })
            }
            catch {
                Write-Result $p $false $_.Exception.Message
            }
        }

        $tgArn = 'arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/oms-pod2-dev-sm-tg/000000000000003e'
        try {
            $health = aws elbv2 describe-target-health --target-group-arn $tgArn --region $AwsRegion --output json 2>$null | ConvertFrom-Json
            if ($health.TargetHealthDescriptions) {
                Write-Host ""
                Write-Host 'ALB SM target health:'
                foreach ($t in $health.TargetHealthDescriptions) {
                    $id = $t.Target.Id
                    $st = $t.TargetHealth.State
                    $desc = $t.TargetHealth.Description
                    $ok = ($st -eq 'healthy')
                    Write-Result "target $id" $ok "$st - $desc"
                    if (-not $ok) { Record-Fail "ALB SM target unhealthy: $desc" }
                }
            }
        }
        catch {
            Write-Host "ALB check failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

# --- Summary ---
Write-Section "Summary"
if ($failures.Count -eq 0) {
    Write-Host 'All checks passed. SM should be reachable via ALB once health check catches up.' -ForegroundColor Green
}
else {
    Write-Host "$($failures.Count) issue(s) found:" -ForegroundColor Red
    foreach ($f in $failures) { Write-Host "  - $f" -ForegroundColor Red }
    Write-Host ""
    Write-Host 'Likely next steps:' -ForegroundColor Yellow
    Write-Host '  1. Harness: confirm sitemanager_server_setup + sitemanager_deploy passed'
    Write-Host '  2. Content server: verify D:\content\pod2\sm has shoplogic files'
    Write-Host '  3. SM server: pod2-dev-sm site must exist and point at UNC sm path'
    Write-Host '  4. Re-run OMS-App-Deploy with webserver_setup_require=true if steps failed'
}

exit $(if ($failures.Count -eq 0) { 0 } else { 1 })

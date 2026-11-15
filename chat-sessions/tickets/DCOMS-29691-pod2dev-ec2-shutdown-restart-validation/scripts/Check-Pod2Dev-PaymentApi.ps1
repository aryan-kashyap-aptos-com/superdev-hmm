$ErrorActionPreference = 'Continue'
Write-Output '=== Payment API DNS check ==='
$paymentDns = 'oms-pod2-dev-paymentapi.dev.eom.aptos.io'
try {
    $dns = Resolve-DnsName $paymentDns -ErrorAction Stop | Select-Object -First 3 Name,IPAddress
    $dns | Format-Table -AutoSize | Out-String | Write-Output
} catch {
    Write-Output "DNS resolve failed: $($_.Exception.Message)"
}

Write-Output '=== Payment API HTTP probe ==='
$urls = @(
    "https://$paymentDns/api/payment/v1",
    "https://$paymentDns/api/payment/v1/creditpayments/auth/",
    "http://localhost/api/payment/v1"
)
foreach ($url in $urls) {
    Write-Output "--- $url ---"
    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20 -Method GET
        Write-Output "Status: $($resp.StatusCode)"
        Write-Output "ContentType: $($resp.Headers['Content-Type'])"
        $snippet = $resp.Content
        if ($snippet.Length -gt 250) { $snippet = $snippet.Substring(0,250) }
        Write-Output "BodyStart: $snippet"
    } catch {
        Write-Output "ERROR: $($_.Exception.Message)"
        if ($_.Exception.Response) {
            try {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $body = $reader.ReadToEnd()
                if ($body.Length -gt 250) { $body = $body.Substring(0,250) }
                Write-Output "BodyStart: $body"
            } catch {}
        }
    }
}

Write-Output '=== IIS websites (payment/pod2) ==='
Get-Website | Where-Object { $_.Name -match 'payment|pod2' } | Format-Table Name,State,PhysicalPath -AutoSize | Out-String | Write-Output

Write-Output '=== Windows services (payment) ==='
Get-Service | Where-Object { $_.Name -match 'payment' -or $_.DisplayName -match 'payment' } | Format-Table Name,Status,DisplayName -AutoSize | Out-String | Write-Output

Write-Output '=== Payment UNC path ==='
$paymentUnc = '\\omspod.aptos.com\pod2-dev\dev\payment'
if (Test-Path $paymentUnc) {
    Write-Output "UNC reachable: $paymentUnc"
    Get-ChildItem $paymentUnc -ErrorAction SilentlyContinue | Select-Object -First 5 Name | Format-Table -AutoSize | Out-String | Write-Output
} else {
    Write-Output "UNC NOT reachable: $paymentUnc"
}

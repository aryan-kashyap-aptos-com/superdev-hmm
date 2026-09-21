$ErrorActionPreference = 'Continue'
$paymentUrl = 'https://oms-pod2-dev-paymentapi.dev.eom.aptos.io/api/payment/v1/creditpayments/authandenroll/'
$body = '{"UserId":1,"CurrencyCode":"USD","Amount":1.00,"OrderNumber":"TEST123456","NewCreditCard":{"UserId":1,"NameOnCard":"Test User","CardNickname":"test","CardNumber":"4111111111111111","CardExpiration":"1228","CVV":"123","BillingFirstName":"Test","BillingLastName":"User","BillingStreet1":"1 Main St","BillingStreet2":"","BillingCity":"New York","BillingState":"NY","BillingZip":"10001","BillingCountry":"US","BillingPhone":"5555555555","BillingEmail":"test@example.com","EncryptedCardNumber":"","EncryptedExpiryMonth":"","EncryptedExpiryYear":"","EncryptedSecurityCode":""}}'

Write-Output "POST $paymentUrl"
try {
    $resp = Invoke-WebRequest -Uri $paymentUrl -Method POST -ContentType 'application/json' -Body $body -UseBasicParsing -TimeoutSec 30
    Write-Output "Status: $($resp.StatusCode)"
    $content = $resp.Content
    if ($content.Length -gt 500) { $content = $content.Substring(0,500) }
    Write-Output "Body: $content"
} catch {
    $status = $null
    if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode }
    Write-Output "Status: $status"
    Write-Output "Error: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $errBody = $reader.ReadToEnd()
            if ($errBody.Length -gt 500) { $errBody = $errBody.Substring(0,500) }
            Write-Output "Body: $errBody"
        } catch {}
    }
}

Write-Output '=== Recent SM log files ==='
$logRoots = @('D:\logs', 'D:\content\dev\sm\logs', '\\omspod.aptos.com\pod2-dev\dev\sm\logs')
foreach ($root in $logRoots) {
    if (Test-Path $root) {
        Write-Output "LOG ROOT: $root"
        Get-ChildItem $root -Recurse -File -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 8 FullName,LastWriteTime,Length |
            Format-Table -AutoSize | Out-String | Write-Output
    }
}
